# README DEL PROYECTO

## SETUP FOR LINUX ONLY
sudo apt install python3-venv freetds-dev gcc build-essential unixodbc-dev freetds-bin python3-tk
chmod +x download_odbc-18.sh
./download_odbc-18.sh
python3 -m venv myEnv
source myEnv/bin/activate
pip install -r requirements.txt
