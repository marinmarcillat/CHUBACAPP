import numpy as np
import sys, os, math
import concurrent.futures
from multiprocessing import Pool, cpu_count
from PyQt5 import QtCore

sys.path.append(os.path.join(os.path.abspath(os.path.join(__file__, "../../..")), 'CloudComPy310\CloudCompare'))
import cloudComPy as cc


class pcdGenThread(QtCore.QThread):
    """Detects the blurry image and store their reference for later suppression"""
    prog_val = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, model, scales, output_path, metrics):
        super(pcdGenThread, self).__init__()
        self.running = True
        self.model = model
        self.scales = scales
        self.output_path = output_path
        self.metrics = metrics
        self.pbar_prog = 1
        self.pbar_tot = len(scales)

    def update_pbar(self, scale):
        self.prog_val.emit(round((self.pbar_prog / self.pbar_tot) * 100))
        print("Scale {} done !".format(scale))
        self.pbar_prog += 1

    def run(self):
        print("Starting topographic metrics processes...")
        nb_processes = min(len(self.scales), cpu_count())
        inputs = ((self.model, scale, self.output_path, self.metrics) for scale in self.scales)
        with Pool(processes=nb_processes) as pool:
            for i in inputs:
                pool.apply_async(thread_generate_pcd, args=i, callback=self.update_pbar)
            pool.close()
            # wait for all tasks to finish
            pool.join()

        print("Done !")
        self.prog_val.emit(0)
        self.finished.emit()
        self.running = False


def calc_tri_bpi(ref, points, a0, a1, a2, a3):
    TRI = 0
    BPI = 0
    d_ref = (a0 * ref[0] + a1 * ref[1] + a2 * ref[2] - a3) / math.sqrt(a0 ** 2 + a1 ** 2 + a2 ** 2)
    for point in points:
        d = (a0 * point[0] + a1 * point[1] + a2 * point[2] - a3) / math.sqrt(
            a0 ** 2 + a1 ** 2 + a2 ** 2)  # Distance to plane
        TRI += abs(d - d_ref)
        BPI += d
    TRI = TRI / len(points)
    BPI = d_ref - (BPI / len(points))
    return TRI, BPI


def thread_cpd_compute(cloud, octree, scale, level):
    np_tri = np.empty(shape=(len(cloud), 1))
    np_bpi = np.empty(shape=(len(cloud), 1))
    for i in range(len(cloud)):
        neighbours = octree.getPointsInSphericalNeighbourhood(cloud[i].tolist(), scale, level)
        points = np.empty(shape=(len(neighbours), 3))
        for j in range(len(neighbours)):
            points[j] = neighbours[j].point

        n_cloud = cc.ccPointCloud("N_cloud")
        n_cloud.coordsFromNPArray_copy(points)
        plane = cc.ccPlane.Fit(n_cloud)
        if plane is not None:
            a0, a1, a2, a3 = plane.getEquation()
            np_tri[i], np_bpi[i] = calc_tri_bpi(cloud[i], points, a0, a1, a2, a3)
        else:
            np_tri[i], np_bpi[i] = np.nan, np.nan
    return [np_tri, np_bpi]


def thread_generate_pcd(model, scale, output_path, metrics):
    slope, aspect, roughness, tri, bpi, gm, gc = metrics
    mesh = cc.loadMesh(model)

    target_nb_neighbours = 10

    density = target_nb_neighbours / (np.pi * scale ** 2)
    density = max(density, 100)  # min density
    density = min(density, 5000)  # max density

    print('Model: {}, scale: {}, density: {}'.format(str(model), str(scale), str(density)))

    cloud = mesh.samplePoints(True, density)
    np_cloud = cloud.toNpArrayCopy()

    if slope or aspect:
        cc.computeNormals([cloud], model=cc.LOCAL_MODEL_TYPES.QUADRIC, defaultRadius=scale)
        cloud.convertNormalToDipDirSFs()

        dic = cloud.getScalarFieldDic()
        if slope:
            dip = cloud.getScalarField(dic['Dip (degrees)'])
            dip.setName('slope_deg_{}_m'.format(str(scale)))
        else:
            cloud.deleteScalarField(dic['Dip (degrees)'])

        dic = cloud.getScalarFieldDic()
        if aspect:
            dip_dir = cloud.getScalarField(dic['Dip direction (degrees)'])
            dip_dir.setName('aspect_deg_{}_m'.format(str(scale)))

            np_dip_dir = dip_dir.toNpArrayCopy()
            north = np.cos(np.deg2rad(np_dip_dir))
            east = np.sin(np.deg2rad(np_dip_dir))
            sf_north_id = cloud.addScalarField('northness_{}_m'.format(str(scale)))
            sf_east_id = cloud.addScalarField('eastness_{}_m'.format(str(scale)))
            sf_north = cloud.getScalarField(sf_north_id)
            sf_east = cloud.getScalarField(sf_east_id)
            sf_north.fromNpArrayCopy(north)
            sf_east.fromNpArrayCopy(east)
        else:
            cloud.deleteScalarField(dic['Dip direction (degrees)'])

    if roughness:
        cc.computeRoughness(scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Roughness ')][0]
        roughness = cloud.getScalarField(dic[key])
        roughness.setName('roughness_{}_m'.format(str(scale)))

    if gc:
        cc.computeCurvature(cc.CurvatureType.GAUSSIAN_CURV, scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Gaussian curvature ')][0]
        gaus_curv = cloud.getScalarField(dic[key])
        gaus_curv.setName('gaus_curv_{}_m'.format(str(scale)))

    if gm:
        cc.computeCurvature(cc.CurvatureType.MEAN_CURV, scale, [cloud])
        dic = cloud.getScalarFieldDic()
        key = [i for i in dic.keys() if i.startswith('Mean curvature ')][0]
        mean_curv = cloud.getScalarField(dic[key])
        mean_curv.setName('mean_curv_{}_m'.format(str(scale)))

    if tri or bpi:
        if tri:
            TRI_id = cloud.addScalarField('TRI_{}_m'.format(str(scale)))  # TRI
            TRI_sf = cloud.getScalarField(TRI_id)

        if bpi:
            BPI_id = cloud.addScalarField('BPI_{}_m'.format(str(scale)))  # BPI
            BPI_sf = cloud.getScalarField(BPI_id)

        octree = cloud.computeOctree(progressCb=None, autoAddChild=True)
        level = octree.findBestLevelForAGivenNeighbourhoodSizeExtraction(scale)

        nb_threads = 8
        np_cld_split = np.array_split(np_cloud, nb_threads)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(thread_cpd_compute, cloud_i, octree, scale, level) for cloud_i in np_cld_split]
            results = [f.result() for f in futures]

        np_tri = np.vstack(list(i[0] for i in results))
        np_bpi = np.vstack(list(i[1] for i in results))
        if tri:
            TRI_sf.fromNpArrayCopy(np_tri)
        if bpi:
            BPI_sf.fromNpArrayCopy(np_bpi)

    exp_pcd_path = os.path.join(output_path, 'cloud_metrics_{}.pcd'.format(str(scale)))
    ret = cc.SavePointCloud(cloud, exp_pcd_path)

    print('Model: {}, scale: {}, Done !'.format(str(model), str(scale)))

    return scale


if __name__ == "__main__":
    model = r"D:\chereef_marin\scripts\example_wall_chereef\MyProcessing_1_mesh.ply"
    metrics = [0,0,0,1,1,0,0]
    scale = 0.02
    output_path = r'D:\chereef_marin\scripts\example_wall_chereef\metrics'

    thread_generate_pcd(model, scale, output_path, metrics)
