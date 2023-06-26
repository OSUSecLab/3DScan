# 3DScan


## Run in docker (working in progress)

```bash
workspace=<workspace>

mkdir -p $workspace
cd $workspace

git clone https://github.com/OSUSecLab/3DScan
wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/AssetStudio.executable.zip"
wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/wine.drive.zip"
wget "https://github.com/OSUSecLab/3DScan/releases/download/dependents/wine.source.zip"
unzip AssetStudio.executable.zip
unzip wine.drive.zip
unzip wine.source.zip

docker rm -f 3dscan
docker run -d -v $workspace:/3DSCANWorkSpace -v $workspace/.wine:/root/.wine -e PATH=/3DSCANWorkSpace/wine-source:$PATH --name 3dscan  ubuntu tail -f /dev/null

docker exec 3dscan root:root -R /3DSCANWorkSpace/.wine
docker exec 3dscan apt update
docker exec 3dscan apt install -y gcc make wget zlib1g-dev
docker exec 3dscan wget https://download.sourceforge.net/libpng/libpng-1.5.13.tar.gz
docker exec 3dscan tar -xf libpng-1.5.13.tar.gz
docker exec 3dscan bash -c "cd libpng-1.5.13; ./configure; make; make install"
docker exec 3dscan ln -s  /usr/local/lib/libpng15.so.15  /usr/lib/x86_64-linux-gnu/libpng15.so.15
```
