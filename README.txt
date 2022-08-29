Implementação de Hosts via FastAPI

Como fiz para colocar no ar:

  git clone https://github.com/pbandierapaiva/dcp
  cd dcp/

  virtualenv venv 
ou
  python -m venv venv

  source venv/bin/activate
  pip  install -r requirements.txt

Se já tiver o ambiente, basta

$ source venv/bin/activate
$ uvicorn hostapi:app --reload
ou
$ uvicorn hostapi:app --reload --host 0.0.0.0
