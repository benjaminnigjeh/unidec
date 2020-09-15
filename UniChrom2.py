import os
import numpy as np
import wx
from pubsub import pub
import unidec_modules.unidectools as ud
from metaunidec.mudpres import MetaUniDecBase
import multiprocessing
from unidec_modules.gui_elements.ChromWindow import ChromWindow
from unidec_modules.isolated_packages import FileDialogs
from unidec_modules.ChromEng import ChromEngine, chrom_file_exts


class ChromApp(MetaUniDecBase):
    def __init__(self, *args, **kwargs):
        """
        Initialize ChromApp
        :param args:
        :param kwargs:
        :return: ChromeApp object
        """
        MetaUniDecBase.__init__(self, *args, **kwargs)
        self.init(*args, **kwargs)

    def init(self, *args, **kwargs):
        self.eng = ChromEngine()
        self.view = ChromWindow(self, "UniChrom", self.eng.config)
        self.import_config()

        pub.subscribe(self.on_get_mzlimits, 'mzlimits')
        self.outputfile = None
        self.scans = None
        self.view.menu.update_recent()
        if False:
            path = "D:\\Data\\ShortCourse\\strepme.RAW"
            #path = "D:\Data\ChromTest\SYJMX160819_04.hdf5"
            self.open_file(path)

    def on_open(self, e=None):
        """
        Open dialog for file opening
        :param e: unused space for event
        :return: None
        """
        dlg = wx.FileDialog(self.view, "Choose an MS data file", '', "", "*.*")
        if dlg.ShowModal() == wx.ID_OK:
            self.open_file(dlg.GetPath())
        dlg.Destroy()

    def on_open_dir(self, e=None):
        dirname = FileDialogs.open_single_dir_dialog("Choose a raw file", '')
        print("Opening Directory: ", dirname)
        if dirname is not None:
            if os.path.splitext(dirname)[1] in chrom_file_exts:
                self.open_file(dirname)

    def open_file(self, path, skip_eng=False):
        self.view.clear_all_plots()
        self.view.ypanel.list.clear_list()
        if os.path.isfile(path) or os.path.isdir(path):
            self.view.SetStatusText("Opening", number=0)
            if not skip_eng:
                load_hdf5 = self.eng.open_chrom(path)
            else:
                load_hdf5 = True
            self.view.SetStatusText(str(self.eng.filename), number=0)
            self.load_to_gui()
            self.makeplotc()
            if load_hdf5:
                self.update_hdf5()
            self.write_to_recent(self.eng.config.hdf_file)
            self.view.menu.update_recent()
        else:
            print("Could not find file:", path)

    def update_hdf5(self, export=True):
        self.view.clear_plots()
        self.eng.reset_vars(export)
        self.view.ypanel.list.populate(self.eng.data)
        self.import_config()
        self.on_replot()
        try:
            self.on_auto_peak_width(set=False)
        except:
            pass

    def on_open_hdf5(self, e=None):
        """
        Open dialog for file opening
        :param e: unused space for event
        :return: None
        """
        dlg = wx.FileDialog(self.view, "Choose an MS data file", '', "", "*.hdf5*")
        if dlg.ShowModal() == wx.ID_OK:
            self.open_hdf5_file(dlg.GetPath())
        dlg.Destroy()

    def open_hdf5_file(self, path):
        result, newpath = self.eng.open_hdf5_file(path)
        if result:
            self.open_file(newpath, skip_eng=True)

    def on_batch_chrom1(self, e=None):
        self.get_from_gui()
        timestarts, timeends = self.eng.get_times()
        print("Batch Run")
        paths = FileDialogs.open_multiple_files_dialog(message="Choose files to batch process.",file_type="*.*")

        for p in paths:
            print(p) # SWITCH TO HDF5
            self.eng.config.write_hdf5(p)
            self.open_file(p)
            self.on_list_add(timestarts, timeends)
            self.on_auto()


    def get_from_gui(self):
        self.eng.config.time_window = float(self.view.ctlmin.GetValue())
        self.eng.config.chrom_peak_width = float(self.view.ctlcpeaks_param1.GetValue())
        pass

    def load_to_gui(self):
        self.view.ctlmin.SetValue(str(self.eng.config.time_window))
        self.view.ctlcpeaks_param1.SetValue(str(self.eng.config.chrom_peak_width))
        pass

    def plot_single_mz(self, e=None):
        self.makeplot4(plot=self.view.plotm, data=self.eng.mzdata)

    def plot_single_mass(self):
        self.makeplot2(plot=self.view.plot2s, data=self.eng.massdat)

    def plot_single_pks(self):
        self.makeplot2(plot=self.view.plot2s, data=self.eng.massdat, pks=self.eng.unidec_eng.pks)
        self.makeplot4(plot=self.view.plotm, data=self.eng.mzdata, pks=self.eng.unidec_eng.pks)

    def on_selection(self, min, max, plot=True):
        self.view.SetStatusText("Averaging Scans...", number=1)
        self.view.SetStatusText("Please wait...", number=2)
        self.eng.get_data_from_times(min, max)
        self.view.SetStatusText("Time: %.2f to %.2f" % (self.eng.scans[2], self.eng.scans[3]), number=1)
        self.view.SetStatusText("Scans: " + str(self.eng.scans[0]) + " to " + str(self.eng.scans[1]), number=2)
        if plot:
            try:
                self.plot_single_mz()
            except (TypeError, IndexError):
                print("Error Plotting Scans")
        return self.eng.mzdata

    def on_unidec_run(self, e=None):
        self.export_config()
        self.eng.unidec_eng.pass_data_in(self.eng.mzdata)
        self.eng.config.config_export(self.eng.unidec_eng.config.confname)
        self.eng.unidec_eng.config.config_import(self.eng.unidec_eng.config.confname)
        self.eng.unidec_eng.process_data()
        self.eng.unidec_eng.run_unidec()

        self.eng.mzdata = self.eng.unidec_eng.data.data2
        self.eng.massdat = self.eng.unidec_eng.data.massdat

        self.plot_single_mz()
        self.plot_single_mass()
        pass

    def on_pick_peaks_individual(self, e=None):
        self.export_config()
        self.eng.config.config_export(self.eng.unidec_eng.config.confname)
        self.eng.unidec_eng.config.config_import(self.eng.unidec_eng.config.confname)
        self.eng.unidec_eng.pick_peaks()
        print(self.eng.unidec_eng.pks.masses)
        self.plot_single_pks()
        self.view.singlepeakpanel.add_data(self.eng.unidec_eng.pks)
        pass

    def on_pick_peaks(self, e=None):
        """
        Tested
        :param e:
        :return:
        """
        self.view.SetStatusText("Picking Peaks...", number=5)
        self.export_config()
        self.eng.pick_peaks()
        self.view.peakpanel.add_data(self.eng.pks)
        self.view.peakpanel.meta = True
        self.makeplot2_mud()
        self.makeplot7()
        self.plot_sums()
        self.view.SetStatusText("Peak Detection and Extraction Complete", number=5)
        pass

    def on_clear_spectra(self, e=None):
        self.eng.data.clear()
        self.update_hdf5()

    def on_manual_add(self, e=None):
        self.eng.add_manual_selection()
        self.update_hdf5()

    def on_list_add(self, starts, ends):
        self.get_from_gui()
        print(starts)
        print(ends)
        self.eng.add_list_times(starts,ends)
        self.update_hdf5()
        pass

    def on_timepart(self, e=None):
        self.get_from_gui()
        self.eng.add_regular_times()
        self.update_hdf5()

    def on_chrom_peaks(self, e=None):
        self.get_from_gui()
        self.eng.add_chrom_peaks()
        self.update_hdf5()

    def on_delete(self, e=None):
        self.makeplot2_mud()

    def on_single_delete(self, e=None):
        self.plot_single_pks()

    def on_single_charge_states(self, e=None):
        self.on_charge_states(self, plot=self.view.plotm, peakpanel=self.view.singlepeakpanel,
                              data=self.eng.unidec_eng.data.data2)

    def on_single_differences(self, e=None):
        self.on_differences(self, plot=self.view.plot2s, peakpanel=self.view.singlepeakpanel,
                            massdat=self.eng.unidec_eng.data.massdat, pks=self.eng.unidec_eng.pks)

    def on_single_label_masses(self, e=None):
        self.on_label_masses(self, peakpanel=self.view.singlepeakpanel, pks=self.eng.unidec_eng.pks,
                             plot=self.view.plot2s, dataobj=self.eng.unidec_eng.data)

    def on_replot(self, e=None, plotsums=True):
        self.export_config()
        self.makeplot1()
        self.makeplot2_mud()
        self.plot_chrom_shading()

    def makeplotc(self, e=None):
        self.view.plotc.plotrefreshtop(self.eng.ticdat[:, 0], self.eng.ticdat[:, 1], title="Total Ion Chromatogram",
                                       xlabel="Time (min)", ylabel="Intensity", zoom="fixed_span")

    def plot_chrom_shading(self, e=None):
        print("Chrom Shading Plot")
        self.makeplotc()
        min = np.amin(self.eng.ticdat[:, 1])
        max = np.amax(self.eng.ticdat[:, 1])
        for s in self.eng.data.spectra:
            if s.ignore == 0:
                tstart = s.attrs["timestart"]
                tend = s.attrs["timeend"]

                print(tstart, tend)
                self.view.plotc.add_rect(tstart, min, tend - tstart, max - min, facecolor=s.color)
        self.view.plotc.repaint()


if __name__ == "__main__":
    '''
    if False:
        import clr
        from System.Threading import ApartmentState, Thread, ThreadStart

        def app_thread():
            multiprocessing.freeze_support()
            app = ChromApp()
            app.start()

        thread = Thread(ThreadStart(app_thread))
        thread.SetApartmentState(ApartmentState.STA)
        thread.Start()
        thread.Join()'''

    multiprocessing.freeze_support()
    app = ChromApp()
    app.start()




