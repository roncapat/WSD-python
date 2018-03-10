#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from PyWSD import wsd_common


class ScannerCondition:
    def __init__(self):
        self.id = 0
        self.time = ""
        self.name = ""
        self.component = ""
        self.severity = ""

    def __str__(self):
        s = ""
        s += "Condition ID:         %d\n" % self.id
        s += "Condition name:       %s\n" % self.name
        s += "Condition time:       %s\n" % self.time
        s += "Condition component:  %s\n" % self.component
        s += "Condition severity:   %s\n" % self.severity
        return s


class ScannerStatus:
    def __init__(self):
        self.time = ""
        self.state = ""
        self.reasons = []
        self.active_conditions = {}  # dict {id, condition}
        self.conditions_history = {}  # dict (time, condition)

    def __str__(self):
        s = ""
        s += "Scanner time:         %s\n" % self.time
        s += "Scanner state:        %s\n" % self.state
        s += "Reasons:              %s\n" % ", ".join(self.reasons)
        s += "Active conditions:\n"
        for ac_id, ac in self.active_conditions.items():
            s += wsd_common.indent(str(ac))
        s += "Condition history:\n"
        for t, c in self.conditions_history.items():
            s += wsd_common.indent(str(c))
            s += wsd_common.indent("Clear time: %s\n" % t)
        return s


class ScannerSettings:
    def __init__(self):
        self.formats = []
        self.compression_factor = (0, 0)  # (min, max)
        self.content_types = []
        self.size_autodetect_sup = False
        self.auto_exposure_sup = False
        self.brightness_sup = False
        self.contrast_sup = False
        self.scaling_range_w = (0, 0)  # (min, max)
        self.scaling_range_h = (0, 0)  # (min, max)
        self.rotations = []

    def __str__(self):
        s = ''
        s += "Supported formats:    %s\n" % ', '.join(self.formats)
        s += "Compression range:    %d - %d\n" % self.compression_factor
        s += "Content types:        %s\n" % ', '.join(self.content_types)
        s += "Size autodetect:      %r\n" % self.size_autodetect_sup
        s += "Auto exposure:        %r\n" % self.auto_exposure_sup
        s += "Manual brightness:    %r\n" % self.brightness_sup
        s += "Manual contrast:      %r\n" % self.contrast_sup
        s += "Width scaling:        %d - %d\n" % self.scaling_range_w
        s += "Height scaling:       %d - %d\n" % self.scaling_range_h
        s += "Rotations:            %s\n" % ', '.join(self.rotations)
        return s


class ScannerSourceSettings:
    def __init__(self):
        self.optical_res = (0, 0)
        self.width_res = []
        self.height_res = []
        self.color_modes = []
        self.min_size = (0, 0)
        self.max_size = (0, 0)

    def __str__(self):
        s = ""
        s += "Optical resolution:   (%d, %d)\n" % self.optical_res
        s += "Width resolutions:    %s\n" % ', '.join(self.width_res)
        s += "Height resolutions:   %s\n" % ', '.join(self.height_res)
        s += "Color modes:          %s\n" % ', '.join(self.color_modes)
        s += "Minimum size:         (%d, %d)\n" % self.min_size
        s += "Maximum size:         (%d, %d)\n" % self.max_size
        return s


class DocumentParams:
    def __init__(self):
        self.format = ""
        self.compression_factor = ""
        self.images_num = 0
        self.input_src = ""
        self.content_type = ""
        self.size_autodetect = False
        self.input_size = (0, 0)
        self.auto_exposure = False
        self.contrast = 0
        self.brightness = 0
        self.sharpness = 0
        self.scaling = (100, 100)
        self.rotation = 0
        self.front = None
        self.back = None

    def __str__(self):
        s = ""
        s += "Format:               %s\n" % self.format
        s += "Compression factor:   %s\n" % self.compression_factor
        s += "Images count:         %d\n" % self.images_num
        s += "Input source:         %s\n" % self.input_src
        s += "Content type:         %s\n" % self.content_type
        s += "Size autodetect:      %r\n" % self.size_autodetect
        s += "Input size:           (%d, %d)\n" % self.input_size
        s += "Auto exposure:        %r\n" % self.auto_exposure
        s += "Contrast:             %d\n" % self.contrast
        s += "Brightness:           %d\n" % self.brightness
        s += "Sharpness:            %d\n" % self.sharpness
        s += "Scaling:              (%d, %d)\n" % self.scaling
        s += "Rotation:             %d\n" % self.rotation
        if self.front is not None:
            s += "Front side:\n"
            s += wsd_common.indent(str(self.front))
        if self.back is not None:
            s += "Back side:\n"
            s += wsd_common.indent(str(self.back))
        return s


class ScanTicket:
    def __init__(self):
        self.job_name = ""
        self.job_user_name = ""
        self.job_info = ""
        self.doc_params = None

    def __str__(self):
        s = ""
        s += "Job name:             %s\n" % self.job_name
        s += "User name:            %s\n" % self.job_user_name
        s += "Job info:             %s\n" % self.job_info
        s += "Document parameters:\n"
        s += wsd_common.indent(str(self.doc_params))
        return s

    def as_map(self):
        return {'JOB_NAME': self.job_name,
                'USER_NAME': self.job_user_name,
                'JOB_INFO': self.job_info,
                'FORMAT': self.doc_params.format,
                'QUALITY_FACTOR': self.doc_params.compression_factor,
                'IMG_NUM': self.doc_params.images_num,
                'INPUT_SRC': self.doc_params.input_src,
                'CONTENT_TYPE': self.doc_params.content_type,
                'SIZE_AUTODETECT': self.doc_params.size_autodetect,
                'INPUT_W': self.doc_params.input_size[0],
                'INPUT_H': self.doc_params.input_size[1],
                'AUTO_EXPOSURE': self.doc_params.auto_exposure,
                'CONTRAST': self.doc_params.contrast,
                'BRIGHTNESS': self.doc_params.brightness,
                'SHARPNESS': self.doc_params.sharpness,
                'SCALING_W': self.doc_params.scaling[0],
                'SCALING_H': self.doc_params.scaling[1],
                'ROTATION': self.doc_params.rotation,
                'FRONT_X_OFFSET': self.doc_params.front.offset[0],
                'FRONT_Y_OFFSET': self.doc_params.front.offset[1],
                'FRONT_SIZE_W': self.doc_params.front.size[0],
                'FRONT_SIZE_H': self.doc_params.front.size[1],
                'FRONT_COLOR': self.doc_params.front.color,
                'FRONT_RES_W': self.doc_params.front.res[0],
                'FRONT_RES_H': self.doc_params.front.res[1],
                'BACK_X_OFFSET': self.doc_params.back.offset[0],
                'BACK_Y_OFFSET': self.doc_params.back.offset[1],
                'BACK_SIZE_W': self.doc_params.back.size[0],
                'BACK_SIZE_H': self.doc_params.back.size[1],
                'BACK_COLOR': self.doc_params.back.color,
                'BACK_RES_W': self.doc_params.back.res[0],
                'BACK_RES_H': self.doc_params.back.res[1]}


class ScanJob:
    def __init__(self):
        self.id = 0
        self.token = ""
        self.f_pixel_line = 0
        self.f_num_lines = 0
        self.f_byte_line = 0
        self.b_pixel_line = None
        self.b_num_lines = None
        self.b_byte_line = None
        self.doc_params = None

    def __str__(self):
        s = ""
        s += "Job id:               %d\n" % self.id
        s += "Job token:            %s\n" % self.token
        s += "Front properties:\n"
        s += "\tPixels/line:          %s\n" % self.f_pixel_line
        s += "\tLines count:          %s\n" % self.f_num_lines
        s += "\tBytes/line:           %s\n" % self.f_byte_line
        if self.b_pixel_line is not None:
            s += "Back properties:\n"
            s += "\tPixels/line:          %s\n" % self.b_pixel_line
            s += "\tLines count:          %s\n" % self.b_num_lines
            s += "\tBytes/line:           %s\n" % self.b_byte_line
        s += "Document parameters:\n"
        s += wsd_common.indent(str(self.doc_params))
        return s


class JobStatus:
    def __init__(self):
        self.id = 0
        self.state = ""
        self.reasons = []
        self.scans_completed = 0
        self.creation_time = ""
        self.completed_time = ""

    def __str__(self):
        s = ""
        s += "Job id:               %d\n" % self.id
        s += "Job state:            %s\n" % self.state
        s += "State reasons:        %s\n" % ', '.join(self.reasons)
        s += "Scans completed:      %d\n" % self.scans_completed
        s += "Job created at:       %s\n" % self.creation_time
        s += "Job completed at:     %s\n" % self.completed_time
        return s


class JobSummary:
    def __init__(self):
        self.name = ""
        self.user_name = ""
        self.status = JobStatus()

    def __str__(self):
        s = ""
        s += "Job name:               %s\n" % self.name
        s += "User name:              %s\n" % self.user_name
        s += str(self.status)
        return s


class MediaSide:
    def __init__(self):
        self.offset = (0, 0)
        self.size = (0, 0)
        self.color = ""
        self.res = (0, 0)

    def __str__(self):
        s = ""
        s += "Offset:               (%d, %d)\n" % self.offset
        s += "Size:                 (%d, %d)\n" % self.size
        s += "Color mode:           %s\n" % self.color
        s += "Resolution:           (%d, %d)\n" % self.res
        return s


class ScannerDescription:
    def __init__(self):
        self.name = ""
        self.info = ""
        self.location = ""

    def __str__(self):
        s = ""
        s += "Scanner name:         %s\n" % self.name
        s += "Scanner info:         %s\n" % self.info
        s += "Scanner location:     %s\n" % self.location
        return s


class ScannerConfiguration:
    def __init__(self):
        self.settings = ScannerSettings()
        self.platen = None
        self.adf_duplex = False
        self.front_adf = None
        self.back_adf = None

    def __str__(self):
        s = ""
        s += str(self.settings)
        if self.platen is not None:
            s += "Platen settings:\n"
            s += wsd_common.indent(str(self.platen))
        if self.front_adf is not None:
            s += "ADF Duplex:           %r\n" % self.adf_duplex
            s += "ADF front settings:\n"
            s += wsd_common.indent(str(self.front_adf))
            if self.adf_duplex:
                s += "ADF back settings:\n"
                s += wsd_common.indent(str(self.back_adf))
        return s
