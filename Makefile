.PHONY: setup lint format test shell coverage test-gold fix-remote \
        run-pipeline run-streamlit clean data-clean logs docker-up docker-down

# ⚙️ Instala dependências do projeto
setup:
	poetry install

# 🔍 Lint do código
lint:
	poetry run task lint

# 🎨 Formata código
format:
	poetry run task format

# 🧪 Roda todos os testes
test:
	poetry run pytest -v --maxfail=1 --disable-warnings

# 🧪 Roda testes com coverage
coverage:
	poetry run pytest --cov=src --cov-report=term-missing

# 🧪 Roda apenas testes da camada Gold
test-gold:
	poetry run pytest -v -k "gold"

# 🐚 Entra no shell do Poetry
shell:
	poetry shell

# ▶️ Executa pipeline Bronze → Silver → Gold
run-pipeline:
	poetry run python src/scpulse/pipeline.py

# 📊 Executa dashboard Streamlit
run-streamlit:
	poetry run streamlit run src/scpulse/pulseboard_visualization/app.py

# 🧹 Limpa arquivos temporários e caches
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov

# 🧹 Limpa diretórios de dados Bronze/Silver/Gold
data-clean:
	rm -rf data/bronze/* data/silver/* data/gold/*

# 📜 Mostra últimos logs
logs:
	tail -f logs/*.log

# 🐳 Sobe serviços do Docker Compose (Kafka, etc.)
docker-up:
	docker compose up -d

# 🐳 Derruba serviços do Docker Compose
docker-down:
	docker compose down


