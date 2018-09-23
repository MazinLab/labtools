import os
import ast
import sys
import pickle
import logging
import warnings
import numpy as np
from datetime import datetime
from matplotlib import pyplot as plt
from configparser import ConfigParser
from scipy.interpolate import interp1d

from mkidpipeline.hotpix import darkHotPixMask
from mkidpipeline.utils.utils import medianStack
from mkidpipeline.utils.loadStack import loadIMGStack
from mkidpipeline.calibration.wavecal import Solution as WaveCalSolution

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Configuration(object):
    """
    Configuration class for the qe measurement.
    """
    def __init__(self, config_directory):
        # some variables that may be needed later
        self._patches = []
        self._lines = []
        self.fig = None
        self.ax = None

        # check to make sure the config file exists
        self.config_directory = config_directory
        self._check_valid_file()

        # read in the configuration file path
        self.config = ConfigParser()
        self.config.read(self.config_directory)

        # check the configuration file format and load the parameters
        self._check_sections()
        self.qe_file = ast.literal_eval(self.config['Data']['qe_file'])
        self.img_directory = ast.literal_eval(self.config['Data']['img_directory'])
        self.wavelengths = ast.literal_eval(self.config['Data']['wavelengths'])
        self.start_time = ast.literal_eval(self.config['Data']['start_time'])
        self.end_time = ast.literal_eval(self.config['Data']['end_time'])
        self.light = ast.literal_eval(self.config['Data']['light'])
        self.dark = ast.literal_eval(self.config['Data']['dark'])
        self.good_pixel = ast.literal_eval(self.config['Data']['good_pixel'])

        self.mkid_area = ast.literal_eval(self.config['Array']['mkid_area'])
        self.y_pixels = ast.literal_eval(self.config['Array']['y_pixels'])
        self.x_pixels = ast.literal_eval(self.config['Array']['x_pixels'])

        self.masks = ast.literal_eval(self.config['Masks']['masks'])
        self.wavecal_file = ast.literal_eval(self.config['Masks']['wavecal_file'])

        self.opt_directory = ast.literal_eval(self.config['Optics']['opt_directory'])
        self.qe_factors = ast.literal_eval(self.config['Optics']['qe_factors'])

        self.out_directory = ast.literal_eval(self.config['Output']['out_directory'])
        self.logging = ast.literal_eval(self.config['Output']['logging'])
        self.verbose = ast.literal_eval(self.config['Output']['verbose'])

        # type check the loaded parameters
        self._check_parameters()
        self._config_changed = False

        # make wavelengths into numpy array
        self.wavelengths = np.array(self.wavelengths)

        if self.light is None:
            # pick light times
            self.light = []
            self._pick_intervals("light")
            self._config_changed = True
        if self.dark is None:
            # pick dark times
            self.dark = []
            self._pick_intervals("dark")
            self._config_changed = True

        if self._config_changed:
            # write new config file
            while True:
                if os.path.isfile(self.config_directory):
                    directory = os.path.dirname(self.config_directory)
                    base_name = "".join(
                        os.path.basename(self.config_directory).split(".")[:-1])
                    suffix = str(os.path.basename(self.config_directory).split(".")[-1])
                    self.config_directory = os.path.join(directory,
                                                         base_name + "_new." + suffix)
                else:
                    break
            self.write(self.config_directory)

    def write(self, file):
        """
        Write configuration object to a file
        """
        try:
            self._check_parameters()
        except Exception as err:
            print(err)
            return
        with open(file, 'w') as f:
            if self.wavecal_file is None:
                wavecal_line = "wavecal_file = {}".format(self.wavecal_file)
                wavecal_line += os.linesep
            else:
                wavecal_line = "wavecal_file = '{}'".format(self.wavecal_file)
                wavecal_line += os.linesep
            f.write("[Data]" + os.linesep +
                    "qe_file = '{}'".format(self.qe_file) + os.linesep +
                    "img_directory = '{}'".format(self.img_directory) + os.linesep +
                    "wavelengths = {}".format(list(self.wavelengths)) + os.linesep +
                    "start_time = {}".format(self.start_time) + os.linesep +
                    "end_time = {}".format(self.end_time) + os.linesep +
                    "light = {}".format(self.light) + os.linesep +
                    "dark = {}".format(self.dark) + os.linesep +
                    "good_pixel = {}".format(self.good_pixel) + os.linesep + os.linesep +
                    "[Array]" + os.linesep +
                    "mkid_area = {}".format(self.mkid_area) + os.linesep +
                    "y_pixels = {}".format(self.y_pixels) + os.linesep +
                    "x_pixels = {}".format(self.x_pixels) + os.linesep + os.linesep +
                    "[Masks]" + os.linesep +
                    "masks = {}".format(self.masks) + os.linesep +
                    wavecal_line + os.linesep +
                    "[Optics]" + os.linesep +
                    "opt_directory = '{}'".format(self.opt_directory) + os.linesep +
                    "qe_factors = {}".format(self.qe_factors) + os.linesep + os.linesep +
                    "[Output]" + os.linesep +
                    "out_directory = '{}'".format(self.out_directory) + os.linesep +
                    "logging = {}".format(self.logging) + os.linesep +
                    "verbose = {}".format(self.verbose) + os.linesep)

    def _pick_intervals(self, name):
        def line_picker(line, mouse_event):
            if mouse_event.xdata is None:
                return False, dict()
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            ind = np.argmin(np.abs(x_data - mouse_event.xdata))
            pick_x = x_data[ind]
            pick_y = y_data[ind]
            props = dict(ind=ind, pick_x=pick_x, pick_y=pick_y)
            return True, props

        def on_pick(event):
            time_list = getattr(self, name)
            if event.pick_x in time_list:
                time_list.remove(event.pick_x)
            else:
                time_list.append(event.pick_x)
                time_list = list(np.sort(time_list))
                setattr(self, name, time_list)
            for patch in self._patches:
                patch.remove()
            for vertical_line in self._lines:
                vertical_line.remove()
            self._patches = []
            self._lines = []
            for ind in range(int(np.floor(len(time_list) / 2))):
                self._patches.append(self.ax.axvspan(time_list[2 * ind],
                                                     time_list[2 * ind + 1],
                                                     color='b', alpha=0.5))
            for ind in range(len(time_list)):
                self._lines.append(self.ax.axvline(time_list[ind], color='b'))
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

        stack = loadIMGStack(self.img_directory, self.start_time, self.end_time,
                             ny=self.y_pixels, nx=self.x_pixels, verbose=False)
        self.fig, self.ax = plt.subplots(figsize=(15, 5))
        self.ax.set_title('pick {} parameter'.format(name))
        times = np.linspace(self.start_time, self.end_time,
                            self.end_time - self.start_time + 1)
        self.ax.plot(times, stack[:, self.good_pixel[1], self.good_pixel[0]],
                     picker=line_picker)
        self.fig.canvas.mpl_connect('pick_event', on_pick)
        plt.show(block=True)
        integer_list = getattr(self, name)
        assert len(integer_list) % 2 == 0, "must choose an even number of points"
        new_list = [[int(integer_list[2 * ind]), int(integer_list[2 * ind + 1])]
                    for ind in range(int(np.floor(len(integer_list) / 2)))]
        setattr(self, name, new_list)

    def _check_valid_file(self):
        assert os.path.isfile(self.config_directory), \
            self.config_directory + " is not a valid configuration file"

    def _check_sections(self):
        section = "{0} must be a configuration section"
        param = "{0} must be a parameter in the configuration file '{1}' section"

        assert 'Data' in self.config.sections(), section.format('Data')
        assert 'qe_file' in self.config['Data'].keys(), \
            param.format('qe_file', 'Data')
        assert 'img_directory' in self.config['Data'].keys(), \
            param.format('img_directory', 'Data')
        assert 'wavelengths' in self.config['Data'].keys(), \
            param.format('wavelengths', 'Data')
        assert 'start_time' in self.config['Data'].keys(), \
            param.format('start_time', 'Data')
        assert 'end_time' in self.config['Data'].keys(), \
            param.format('end_time', 'Data')
        assert 'light' in self.config['Data'].keys(), \
            param.format('light', 'Data')
        assert 'dark' in self.config['Data'].keys(), \
            param.format('dark', 'Data')
        assert 'good_pixel' in self.config['Data'].keys(), \
            param.format('good_pixel', 'Data')

        assert 'Array' in self.config.sections(), section.format('Array')
        assert 'mkid_area' in self.config['Array'].keys(), \
            param.format('mkid_area', 'Array')
        assert 'y_pixels' in self.config['Array'].keys(), \
            param.format('y_pixels', 'Array')
        assert 'x_pixels' in self.config['Array'].keys(), \
            param.format('x_pixels', 'Array')

        assert 'Masks' in self.config.sections(), section.format('Masks')
        assert 'masks' in self.config['Masks'].keys(), \
            param.format('masks', 'Masks')
        assert 'wavecal_file' in self.config['Masks'].keys(), \
            param.format('wavecal_file', 'Masks')

        assert 'Optics' in self.config.sections(), section.format('Optics')
        assert 'opt_directory' in self.config['Optics'].keys(), \
            param.format('opt_directory', 'Optics')
        assert 'qe_factors' in self.config['Optics'].keys(), \
            param.format('qe_factors', 'Optics')

        assert 'Output' in self.config.sections(), section.format('Output')
        assert 'out_directory' in self.config['Output'], \
            param.format('out_directory', 'Output')
        assert 'logging' in self.config['Output'], \
            param.format('logging', 'Output')
        assert 'verbose' in self.config['Output'], \
            param.format('verbose', 'Output')

    def _check_parameters(self):
        assert type(self.qe_file) is str, "qe_file parameter must be a string"

        assert os.path.isfile(self.qe_file), \
            "{0} parameter is not a valid file".format(self.qe_file)

        assert type(self.img_directory) is str, \
            "img_directory parameter must be a string"

        assert os.path.isdir(self.img_directory), \
            "{0} is not a valid directory".format(self.img_directory)

        assert isinstance(self.wavelengths, (list, np.ndarray)), \
            "wavelengths parameter must be a list."
        for index, lambda_ in enumerate(self.wavelengths):
            if type(lambda_) is int:
                self.wavelengths[index] = float(self.wavelengths[index])
            assert isinstance(self.wavelengths[index], (float, np.float)), \
                "elements in wavelengths parameter must be floats or integers."

        assert type(self.start_time) is int, "start_time parameter must be an integer"

        assert type(self.end_time) is int, "end_time parameter must be an integer"

        assert self.end_time - self.start_time > 0, \
            "end_time parameter must be larger than start_time parameter"

        if self.light is not None:
            message = "light parameter must be a list of length two lists of integers"
            assert type(self.light) is list, message
            second_message = ("light parameter must have as many 2 element lists as the "
                              "length of the wavelengths parameter")
            assert len(self.light) == len(self.wavelengths), second_message
            for interval in self.light:
                assert type(interval) is list, message
                assert len(interval) == 2, message
                for integer in interval:
                    assert type(integer) is int, message

        if self.dark is not None:
            message = "dark parameter must be a list of length two lists of integers"
            assert type(self.dark) is list, message
            second_message = ("light parameter must have as many 2 element lists as the "
                              "length of the wavelengths parameter")
            assert len(self.light) == len(self.wavelengths), second_message
            for interval in self.dark:
                assert type(interval) is list, message
                assert len(interval) == 2, message
                for integer in interval:
                    assert type(integer) is int, message

        message = "good_pixel parameter must be a length two list of integers"
        assert type(self.good_pixel) is list, message
        assert len(self.good_pixel) == 2, message
        for integer in self.good_pixel:
            assert type(integer) is int, message

        if type(self.mkid_area) is int:
            self.mkid_area = float(self.mkid_area)
        assert type(self.mkid_area) is float, \
            "mkid_area parameter must be a float or integer"

        assert type(self.y_pixels) is int, "y_pixels parameter must be an integer"

        assert type(self.x_pixels) is int, "x_pixels parameter must be an integer"

        if 'wavelength_cal' in self.masks and self.wavecal_file is None:
            message = ("wavecal_file must not be None if wavelength_cal is specified "
                       "as a mask")
            raise ValueError(message)
        assert type(self.masks) is list, "masks parameter must be a list of strings"
        for mask in self.masks:
            assert type(mask) is str, "masks parameter must be a list of strings"
            mask_list = ['hot_and_cold', 'hot', 'wavelength_cal', 'dark_threshold']
            assert mask in mask_list, "{0} is not a valid mask name".format(mask)
            if mask == 'wavelength_cal':
                assert os.path.isfile(self.wavecal_file), \
                    "{0} is not a valid file".format(self.wavecal_file)

        assert type(self.opt_directory) is str, \
            "opt_directory parameter must be a string"
        assert os.path.isdir(self.opt_directory), \
            "{0} is not a valid directory".format(self.opt_directory)

        message = "qe_factors parameter must be a list of file names and numbers" + \
                  " between 0 and 1"
        assert type(self.qe_factors) is list, message
        for element in self.qe_factors:
            if type(element) is str:
                directory = os.path.join(self.opt_directory, element)
                assert os.path.isfile(directory), \
                    "{0} is not a valid file".format(directory)
            elif type(element) is int or type(element) is float:
                assert (0 <= element <= 1), message
            else:
                raise ValueError(message)

        assert type(self.logging) is bool, "logging parameter must be a boolean"

        assert type(self.out_directory) is str, \
            "out_directory parameter must be a string"
        assert os.path.isdir(self.out_directory), \
            "{0} is not a valid directory".format(self.out_directory)

        assert type(self.verbose) is bool, "verbose parameter must be a boolean"


class Measurement(object):
    """
    Class for holding the information of a qe measurement and running the analysis. After
    the Measurement object is initialized with the configuration file, run_analysis()
    should be run to compute the qe solution.

    Args:
        config_object: object containing the measurement setup (Configuration class)
    """
    def __init__(self, config_object, time_stamp=None):
        # record start time in log file name
        if time_stamp is None:
            self.time_stamp = str(datetime.utcnow().timestamp()).split('.')[0]
        else:
            self.time_stamp = time_stamp

        # define the configuration file path
        self.cfg = config_object

        # log the config file
        log.debug("QE Measurement object created")
        with open(self.cfg.config_directory, "r") as file_:
            config_text = file_.read()
        log.debug("configuration file used:" + os.linesep + config_text)

        # initialize internal variables
        self.pd_irradiance = None
        self.qe = []
        self.qe_masks = []
        self.plot_array = None
        self.wvl_theory = None
        self.qe_theory = None

    def run_analysis(self, plot=True, save=True):
        """
        Run through all the steps in the qe analysis.

        Args:
            plot: determines if a qe plot is generated (boolean)
            save: determines if solution file (and plot) is (are) saved
        """
        try:
            self.load_data()
            self.compute_qe()
            self.compute_theory()

            if save:
                self.save_data()
            if plot:
                self.plot_qe(save=save)
        except KeyboardInterrupt:
            print(os.linesep + "Shutdown requested ... exiting")

    def load_data(self):
        """
        Load measurement text file and save photodiode irradiance.
        """
        # load txt
        qe_data = np.loadtxt(self.cfg.qe_file)

        # make mask to ignore wavelengths not specified in the configuration file
        qe_wavelengths = qe_data[:, 0]
        mask = np.in1d(qe_wavelengths, self.cfg.wavelengths)

        # photo diode properties
        pd_flux = qe_data[mask, 4] * 1e7  # photons / s
        pd_area = 0.00155179165  # m^2
        self.pd_irradiance = pd_flux / pd_area  # photons / m^2 / s

        log.info("loaded {0}".format(self.cfg.qe_file))

    def compute_qe(self):
        """
        Compute the quantum efficiency at each wavelength
        """
        for index, wavelength in enumerate(self.cfg.wavelengths):
            log.info('computing qe for {0} nm'.format(wavelength))
            # load light and dark stacks
            light_stack = loadIMGStack(self.cfg.img_directory, self.cfg.light[index][0],
                                       self.cfg.light[index][1], nx=self.cfg.x_pixels,
                                       ny=self.cfg.y_pixels, verbose=False)
            dark_stack = loadIMGStack(self.cfg.img_directory, self.cfg.dark[index][0],
                                      self.cfg.dark[index][1], nx=self.cfg.x_pixels,
                                      ny=self.cfg.y_pixels, verbose=False)

            # median data
            median_light = medianStack(light_stack)
            median_dark = medianStack(dark_stack)

            # mask data
            self.qe_masks.append(self.make_mask(dark_stack, light_stack, wavelength))
            median_light[self.qe_masks[-1]] = np.nan
            median_dark[self.qe_masks[-1]] = np.nan

            mkid_irradiance = (median_light - median_dark) / self.cfg.mkid_area
            qe = mkid_irradiance / self.pd_irradiance[index]

            with warnings.catch_warnings():
                # nan values will give an unnecessary RuntimeWarning
                warnings.simplefilter("ignore", category=RuntimeWarning)
                logic = np.logical_or(qe < 0, qe > 1)
            self.qe_masks[-1][logic] = 1
            qe[logic] = np.nan

            log.info('{0} pixels passed the cuts'
                          .format(np.sum(self.qe_masks[-1] == 0)))

            self.qe.append(qe)

    def make_mask(self, dark_stack, light_stack, wavelength):
        """
        Make a mask for the stack to remove unwanted pixels
        """
        masks = []
        # always mask out pixels with no counts
        no_counts_mask = np.zeros(light_stack[0].shape, dtype=int)
        no_counts_mask[light_stack[0] == 0] = 1
        masks.append(no_counts_mask)

        if 'hot_and_cold' in self.cfg.masks:
            masks.append(darkHotPixMask.makeDHPMask(stack=dark_stack, maxCut=2400,
                                                    coldCut=False))
            masks.append(darkHotPixMask.makeDHPMask(stack=light_stack, maxCut=2400,
                                                    coldCut=True))

        if 'hot' in self.cfg.masks:
            masks.append(darkHotPixMask.makeDHPMask(stack=dark_stack, maxCut=2400,
                                                    coldCut=False))
            masks.append(darkHotPixMask.makeDHPMask(stack=light_stack, maxCut=2400,
                                                    coldCut=False))

        if 'dark_threshold' in self.cfg.masks:
            dark_mask = np.zeros(dark_stack[0].shape, dtype=int)
            for (row, column), _ in np.ndenumerate(dark_stack[0]):
                if max(dark_stack[:, row, column]) > 100:
                    dark_mask[row, column] = 1
            masks.append(dark_mask)

        if 'wavelength_cal' in self.cfg.masks:
            # load data
            wave_cal = WaveCalSolution(self.cfg.wavecal_file)
            wavecal_mask = np.zeros(dark_stack[0].shape, dtype=int)
            for pixel, _ in np.ndenumerate(dark_stack[0]):
                # mask data if energy - phase fit failed
                if not wave_cal.has_good_energy_solution(pixel=pixel):
                    wavecal_mask[pixel] = 1
                # mask data if histogram fit failed
                if not wave_cal.has_good_histogram_solution(wavelength, pixel=pixel):
                    wavecal_mask[pixel] = 1

            # add wavecal mask to the masks list
            masks.append(wavecal_mask)

        if len(masks) == 0:
            mask = np.ones(dark_stack[0].shape, dtype=int)
            return mask
        else:
            mask = masks[0]
            for current_mask in masks:
                mask = np.logical_or(current_mask, mask)
            return mask

    def plot_mask(self, wavelength_index):
        """
        Plot and show mask grid. Ones are bad pixels. Zeros are good pixels.
        """
        fig, ax = plt.subplots()
        self.plot_array = self.qe_masks[wavelength_index]
        im = ax.imshow(np.array(self.plot_array), aspect='equal')
        ax.format_coord = Formatter(im)
        fig.colorbar(im)
        plt.show(block=False)

    def plot_qe_grid(self, wavelength_index):
        """
        Plot qe on the array grid.
        """
        fig, ax = plt.subplots()
        self.plot_array = self.qe[wavelength_index]
        im = ax.imshow(self.plot_array, aspect='equal')
        ax.format_coord = Formatter(im)
        plt.colorbar(im)
        plt.show(block=False)

    def compute_theory(self):
        """
        Compute the theoretical qe.
        """
        self.wvl_theory = np.linspace(min(self.cfg.wavelengths),
                                      max(self.cfg.wavelengths),
                                      len(self.cfg.wavelengths) * 100)
        qe = np.ones(len(self.wvl_theory))
        for factor in self.cfg.qe_factors:
            if type(factor) is int or type(factor) is float:
                qe *= factor
            elif type(factor) is str:
                # load file
                file_ = os.path.join(self.cfg.opt_directory, factor)
                try:
                    data = np.loadtxt(file_)
                except ValueError:
                    message = 'could not load {0} with numpy.loadtxt()'
                    raise ValueError(message.format(file_))
                wavelengths = data[:, 0]
                multipliers = data[:, 1]

                # check that loaded data makes sense
                if np.logical_or(multipliers > 1, multipliers < 0).any():
                    message = "second column of {0} not normalized between 0 and 1"
                    raise ValueError(message.format(file_))
                max_wvl = max(wavelengths)
                min_wvl = min(wavelengths)
                if np.logical_or(min_wvl > min(self.cfg.wavelengths),
                                 max_wvl < max(self.cfg.wavelengths)):
                    message = "{0} only covers the range ({1}, {2}) nm. Data was " + \
                              "requested outside of the bounds and extrapolated"
                    warnings.warn(message.format(file_, min_wvl, max_wvl))

                # interpolate for each requested wavelength
                ind = np.argsort(wavelengths)
                wavelengths = wavelengths[ind]
                multipliers = multipliers[ind]
                interp = interp1d(wavelengths, multipliers, fill_value='extrapolate')

                qe *= interp(self.wvl_theory)

        self.qe_theory = qe

    def plot_qe(self, save=False):
        """
        Plot the measured and theoretical qe
        """
        fig, ax = plt.subplots()

        qe_median = np.array([np.nanmedian(qe.flatten()) for qe in self.qe])
        qe_upper = np.array([qe_median[ind] + np.nanstd(qe.flatten())
                             for ind, qe in enumerate(self.qe)])
        qe_lower = np.array([qe_median[ind] - np.nanstd(qe.flatten())
                             for ind, qe in enumerate(self.qe)])

        ax.plot(self.cfg.wavelengths, qe_median * 100, linewidth=3, color='black',
                label=r'Measured')
        ax.fill_between(self.cfg.wavelengths, qe_lower * 100, qe_upper * 100,
                        where=qe_upper >= qe_lower, color='green', facecolor='green',
                        interpolate='True', alpha=0.1)
        ax.plot(self.wvl_theory, 100 * self.qe_theory, linestyle='-.', linewidth=2,
                color='black', label=r'Theoretical')

        ax.set_xlabel(r'Wavelength (nm)')
        ax.set_ylabel(r'QE (%)')
        ax.legend()
        ax.set_xlim([min(self.cfg.wavelengths), max(self.cfg.wavelengths)])
        ax.set_ylim([0, max(qe_upper) * 100 * 1.2])

        if save:
            file_name = os.path.join(self.cfg.out_directory, self.time_stamp + '.pdf')
            plt.savefig(file_name, format='pdf')
            plt.close(fig)
        else:
            plt.show(block=False)

    def save_data(self):
        """
        Save Measurement instance in a pickle file
        """
        save_name = os.path.join(self.cfg.out_directory, self.time_stamp + '.p')
        with open(save_name, 'wb') as file_:
            pickle.dump(self, file_)

    # def _format_coordinates(self, x, y):
    #     shape = self.qe[0].shape
    #     col = int(x + 0.5)
    #     row = int(y + 0.5)
    #     if 0 <= col < shape[1] and 0 <= row < shape[0]:
    #         z = self.plot_array[row, col]
    #         return '(%1.0f, %1.0f) z=%1.0f' % (col, row, z)
    #     else:
    #         return '(%1.0f, %1.0f)' % (col, row)


class Formatter(object):
    """
    Custom formatting class for mouse over text
    """
    def __init__(self, im):
        self.im = im

    def __call__(self, x, y):
        return '({:1.0f}, {:1.0f})'.format(x, y)


if __name__ == '__main__':
    # get current time
    time = str(datetime.utcnow().timestamp()).split('.')[0]

    # make config file
    config = Configuration(sys.argv[1])

    # setup logging
    log.propagate = False
    if config.logging:
        log_directory = os.path.join(config.out_directory, 'logs')
        log_file = os.path.join(log_directory, '{}.log'.format(time))
        if not os.path.isdir(log_directory):
            os.mkdir(log_directory)
        file_handler = logging.FileHandler(log_file)
        log_format = '%(asctime)s : %(funcName)s() : %(levelname)s : %(message)s'
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel("DEBUG")
        log.addHandler(file_handler)

    if config.verbose:
        stdout_handler = logging.StreamHandler(sys.stdout)
        log_format = "%(funcName)s() : %(message)s"
        stdout_handler.setFormatter(logging.Formatter(log_format))
        stdout_handler.setLevel("INFO")
        log.addHandler(stdout_handler)

    # run analysis
    measurement = Measurement(config, time_stamp=time)
    measurement.run_analysis(plot=True, save=True)
