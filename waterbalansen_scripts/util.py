import os
import time
import zipfile


def unzip_file(src, dst, force=False, preserve_datetime=False):
    if os.path.exists(dst):
        if not force:
            print(
                "File not unzipped. Destination already exists. Use 'force=True' to unzip."
            )
            return
    if preserve_datetime:
        zipf = zipfile.ZipFile(src, "r")
        for f in zipf.infolist():
            zipf.extract(f, path=dst)
            date_time = time.mktime(f.date_time + (0, 0, -1))
            os.utime(os.path.join(dst, f.filename), (date_time, date_time))
        zipf.close()
    else:
        zipf = zipfile.ZipFile(src, "r")
        zipf.extractall(dst)
        zipf.close()
    return 1


def unzip_changed_files(
    zipname, pathname, check_time=True, check_size=False, debug=False
):
    # Extract each file in a zip-file only when the properties are different
    # With the default arguments this method only checks the modification time
    with zipfile.ZipFile(zipname) as zf:
        infolist = zf.infolist()
        for info in infolist:
            fname = os.path.join(pathname, info.filename)
            extract = False
            if os.path.exists(fname):
                if check_time:
                    tz = time.mktime(info.date_time + (0, 0, -1))
                    tf = os.path.getmtime(fname)
                    if tz != tf:
                        extract = True
                if check_size:
                    sz = info.file_size
                    sf = os.path.getsize(fname)
                    if sz != sf:
                        extract = True
            else:
                extract = True
            if extract:
                if debug:
                    print("extracting {}".format(info.filename))
                zf.extract(info.filename, pathname)
                # set the correct modification time
                # (which is the time of extraction by default)
                tz = time.mktime(info.date_time + (0, 0, -1))
                os.utime(os.path.join(pathname, info.filename), (tz, tz))
