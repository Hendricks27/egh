import os
import sys
import stat
import shutil


for f in ["./linux", "./macarm"]:
    try:
        shutil.rmtree(f)
    except:
        pass
    os.mkdir(f)


required_bin = ["bedGraphToBigWig", "wigToBigWig"]

for b in required_bin:
    durl = "https://hgdownload.soe.ucsc.edu/admin/exe/linux.x86_64/" + b
    cmd = "wget %s -P ./linux/" % durl
    os.system(cmd)

    durl = "https://hgdownload.soe.ucsc.edu/admin/exe/macOSX.arm64/" + b
    cmd = "wget %s -P ./macarm" % durl
    os.system(cmd)


for folder in ["./linux/", "./macarm/"]:

    for f in os.listdir(folder):
        fp = folder + f
        print(fp)

        st = os.stat(fp)
        print(st.st_mode)
        os.chmod(fp, 0o777)
        print(st.st_mode)


