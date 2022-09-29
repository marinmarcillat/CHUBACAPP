import numpy as np

# You can add your camera here:

config_camera = {
    'otus2' : {
        # -> Camera matrix
        'optical_camera_matrix' : np.array([[6600, 0, 3032], [0, 6600, 1986], [0, 0, 1]], dtype='f'),
        # -> Distortion coefficients
        'dist_coeff' : np.array([0.0694682, 0.108887, 0, 0, -0.091225], dtype='f'),
        # -> Original resolution (width, height)
        'resolution' : (6000, 4000),
    },
    'new_camera': {
        # -> Camera matrix
        'optical_camera_matrix': np.array([[0, 0, 0], [0, 0, 0], [0, 0, 1]], dtype='f'),
        # -> Distortion coefficients
        'dist_coeff': np.array([0, 0, 0, 0, 0], dtype='f'),
        # -> Original resolution (width, height)
        'resolution': (1920, 1080),
    }
}
