import subprocess
import os, random
import string, time
import zipfile
import tempfile
import psutil, signal

TIMEOUT = 60 * 60 # 1 hour
MAX_VIRTUAL_MEMORY =  6 * 1024 * 1024 * 1024 # 6 GB
WINEFOLDER = os.path.expanduser('~')  + "/.wine/drive_c/"
AssetStudioGUIPATH = "/opt/AssetStudio/AssetStudioGUI.exe"

def randomName():
  return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def runOnFolder(input_folder, output_folder):

  new_input_name, new_output_name = randomName(), randomName()
  new_input_folder  = WINEFOLDER + "/" + new_input_name
  new_output_folder = WINEFOLDER + "/" + new_output_name

  os.symlink(input_folder, new_input_folder)
  os.symlink(output_folder, new_output_folder)
  #os.system("ls -l %s" % WINEFOLDER)

  try:
    cmd = '"%s" "%s" "%s" "%s"' % ("wine64", AssetStudioGUIPATH, "c:/%s" % new_input_name, "c:/%s" % new_output_name)
    #print(cmd)
    print("[*] extracting models")
    process =  subprocess.Popen(
            cmd, 
            shell=True, 
            stdin=None, 
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
					  #preexec_fn=limit_virtual_memory
          )
    #print(process.pid)
    with open(output_folder+"/PID", "w") as f:
      f.write(str(process.pid))

    timeouted = False
    ret = None
    ttimeout = 0
    tpor = psutil.Process(process.pid)
    pgid = os.getpgid(process.pid) 
    pgs = []
    while True:
      ttimeout += 10
      try:
          ret = process.communicate(timeout=10)
      except subprocess.TimeoutExpired:
        pass

      if ret: break
      pgs = []
      for ttp in psutil.process_iter():
        if os.getpgid(ttp.pid) == pgid:
          pgs.append( ttp )

      try:
        ram = sum([i.memory_info().rss for i in pgs])
        print("[*] pid(%s) time(%s) ram(%s)" % (process.pid, ttimeout, int(ram/1024**2)))
        if ttimeout > TIMEOUT or ram > MAX_VIRTUAL_MEMORY:
          print("[-] %s, killing..." % ("timeout" if ttimeout < 0 else "exceed ram pid(%s) %s" % (process.pid, ram/1024**2)))
          os.killpg(os.getpgid(process.pid), signal.SIGTERM)
          time.sleep(2)
          timeouted = True
      except Exception as e:
        print("[-] error when killing...")

    return process.returncode, ret, timeouted
  finally:
    os.unlink(new_output_folder)
    os.unlink(new_input_folder)

def runOnAPK(apk_path, output_folder, tmp_folder):

  with tempfile.TemporaryDirectory(prefix=tmp_folder+"/") as tfolder:
    print("[*] extracting apk")
    with zipfile.ZipFile(apk_path, "r") as archive:
      for file in archive.namelist():
        if file.startswith('assets/'):
            archive.extract(file, tfolder)
    
    return runOnFolder(tfolder, output_folder)

if __name__ == "__main__":
  output_folder = "/tmp/PoshToffeeGames"
  apk_path = "/opt/samples/MovingSoldier.apk.zip"
  apk_path = "/opt/samples/com.PoshToffeeGames.BunkerZ.zip"
  process = runOnAPK(apk_path, output_folder, output_folder)
  print("!!!", process)

