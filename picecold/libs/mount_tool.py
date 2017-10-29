import re
import subprocess

blkid_dict = dict()


def read_blkid(dev_filter=None):
    output_elements = str(subprocess.check_output("sudo blkid", shell=True, universal_newlines=True)).split()
    key = None
    for el in output_elements:
        if el[len(el) - 1] == ':':
            if dev_filter is None or re.match(dev_filter, el[0:len(el) - 1]):
                key = el[0:len(el) - 1]
                blkid_dict[key] = dict()
        elif key is not None:
            pair_delim_pos = el.find('=')
            blkid_dict[key][el[0:pair_delim_pos]] = el[pair_delim_pos + 2:-1]


def is_plugged_in(dev_or_uuid):
    if dev_or_uuid in blkid_dict:
        return True
    else:
        for dev in blkid_dict:
            if 'UUID' in blkid_dict[dev].keys() and blkid_dict[dev]['UUID'] == dev_or_uuid:
                return True
    return False


def get_dev(uuid) -> str:
    for dev in blkid_dict:
        if 'UUID' in blkid_dict[dev].keys() and blkid_dict[dev]['UUID'] == uuid:
            return dev
    return ""


def mount(dev, mnt_point, opt="") -> bool:
    subprocess.call("sudo mkdir {mnt}".format(mnt=mnt_point), shell=True)
    err_code = subprocess.call("sudo mount {dev} {mnt} {opt}"
                               .format(dev=dev, mnt=mnt_point, opt="" if opt == "" else "-o " + opt), shell=True)
    if err_code == 0:
        return True
    else:
        return False


def umount(dev) -> bool:
    err_code = subprocess.call('sudo umount {dev}'.format(dev=dev), shell=True)
    if err_code == 0:
        return True
    else:
        return False


def get_mount_points(dev_filter="/dev/.*") -> dict:
    mounted_devs = {}
    dev_lines = str(subprocess.check_output("mount -l", shell=True, universal_newlines=True)).split('\n')
    for dev_line in dev_lines:
        kw_pos = dev_line.find("on")
        if kw_pos == -1 and dev_line != '':
            raise LookupError("Could not parse: Unknown format of \"mount -l\" output. Missing \"on\"-keyword.")
        else:
            dev = dev_line[0:kw_pos - 1]
            if re.match(dev_filter, dev):
                mounted_devs[dev] = dev_line[kw_pos + 3:dev_line.find(' ', kw_pos + 3)]
    return mounted_devs
