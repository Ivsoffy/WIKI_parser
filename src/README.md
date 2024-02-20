# Team 00 - Python Bootcamp

## Magical connections

<h2 id="docker" >Запуск докера</h2>

```bash
docker run --name neo4j -p 7687:7687 -d -e NEO4J_AUTH=neo4j/password neo4j:latest
```
<h2 id="venv" >Создание виртуального окружения</h2>

```bash
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
<h2 id="env" >.env файл</h2>

```
URI=bolt://localhost:7687
USER_NAME=neo4j
PASSWORD=password
```

<h2 id="neo4j" >Установка neo4j</h2>

```bash
wget --no-check-certificate -O - https://debian.neo4j.org/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.org/repo stable/' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo service neo4j start
```

<h2 id="edges" >Отображение графа в neo4j</h2>

```
MATCH (n:URL)-[:CONNECTED]->(m:URL)
RETURN n, m
```
