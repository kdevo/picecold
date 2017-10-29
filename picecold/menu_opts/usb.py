import config
import libs.mount_tool as mount_tool
from libs.dot_extended.base import MenuOptionSwitcher
from libs.dot_extended.dialogs import SimpleDialog, StatusMessage


class MountedUsbDevice:
    def __init__(self, dev, mnt):
        self._dev = dev
        self._mnt = mnt

    @property
    def mount_path(self):
        return self._mnt

    @property
    def device_path(self):
        return self._mnt


class UsbHelper:
    def __init__(self, cfg: config.Configuration):
        self._cfg = cfg

    @staticmethod
    def is_usb_plugged_in():
        UsbHelper.refresh()
        return len(mount_tool.blkid_dict) > 0

    @staticmethod
    def refresh():
        mount_tool.read_blkid("/dev/sd.+")

    def find_trusted_usb(self) -> MountedUsbDevice:
        """Finds the first trusted USB stick

        Returns:
            The path of the found transaction or else...

        Raises:
            LookupError: If no trusted USB stick could be found AND mounted
        """
        devs_dict = mount_tool.blkid_dict
        for dev in mount_tool.blkid_dict:
            if self._cfg.is_trusted_uuid(devs_dict[dev]['UUID']):
                mount_target = "/media/{uuid}".format(uuid=devs_dict[dev]['UUID'])
                if mount_tool.get_mount_points().get(dev) or \
                        mount_tool.mount(dev, mount_target, "umask=000"):
                    return MountedUsbDevice(dev, mount_target)
        raise LookupError("Could not mount any device because no USB stick is in the list of trusted devices.")


class UsbTrusting(MenuOptionSwitcher):
    def __init__(self, backlight, cfg: config.Configuration):
        super().__init__()
        self._usb_handler = UsbHelper(cfg)
        self._untrusted_dev = None
        self._backlight = backlight
        self._cfg = cfg

    def begin(self):
        if self._usb_handler.is_usb_plugged_in():
            devs_dict = mount_tool.blkid_dict
            untrusted_dev = None
            for dev in devs_dict:
                if not self._cfg.is_trusted_uuid(devs_dict[dev]['UUID']):
                    untrusted_dev = dev
                    break
            if untrusted_dev is None:
                self.switch(StatusMessage(["Please note",
                                           "Stick(s) are already on the list of trusted devices.",
                                           "{button}"], self._backlight))
            else:
                self.switch(SimpleDialog(["Trust stick?",
                                          "Trust {dev} labeled with \"{lbl}\"?"
                                         .format(dev=untrusted_dev,
                                                 lbl=devs_dict[untrusted_dev].get('LABEL')),
                                          "{answers}"],
                                         callback_on_positive=lambda:
                                         self.on_trust(devs_dict[untrusted_dev]['UUID'],
                                                       devs_dict[untrusted_dev].get('LABEL')),
                                         callback_on_negative=lambda: self.on_abort()))

        else:
            self.switch(StatusMessage(["Information", "No USB stick has been found.", "{button}"],
                                      self._backlight))

    def on_trust(self, uuid, lbl):
        self._cfg.add_trusted_uuid(uuid)
        self.switch(StatusMessage(["Success",
                                   "Added device ({0}) to the list of trusted devices. "
                                   "It will be mounted automatically by this plugin."
                                  .format("UUID: " + uuid if lbl is None else "LABEL: " + lbl),
                                   "{button}"], self._backlight))
        return False

    def on_abort(self):
        self.cleanup()
        return True


class UsbEject(SimpleDialog):
    def __init__(self):
        super().__init__(["Eject?".center(16), "Mounted USB stick(s) will be unmounted.", "{answers}"])

    def select(self):
        if self.selected_answer == self.positive:
            for dev in mount_tool.get_mount_points():
                mount_tool.umount(dev)
        return self.selected_answer is not None
