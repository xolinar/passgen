# Makefile — тулинг для Conventional Commits: Commitizen + commitlint + pre-commit
#
# Использование:
#   make setup-commits   ## установить хуки pre-commit (prepare-commit-msg, commit-msg)
#   make commit          ## интерактивный мастер (Commitizen, через git-cz)
#   make lint-commits    ## провалидировать последний коммит (или диапазон FROM..TO)

# --- Шелл и строгий режим ------------------------------------------------------
SHELL        := /usr/bin/env
.SHELLFLAGS  := bash -Eeuo pipefail -c
.ONESHELL:

# --- Конфигурация путей --------------------------------------------------------
ROOT_DIR          := $(shell git rev-parse --show-toplevel 2>/dev/null)
ifeq ($(strip $(ROOT_DIR)),)
  $(error Не удалось определить корень git. Установите git и запускайте make внутри репозитория)
endif

COMMITS_DIR       := $(ROOT_DIR)/tools/commits
COMMITLINT_CONFIG := $(COMMITS_DIR)/commitlint.config.mjs
COMMIT_HOOK_TYPES := prepare-commit-msg commit-msg

# Локальные бинарники (если вдруг установлены)
NODE_BIN          := $(COMMITS_DIR)/node_modules/.bin
CZ_LOCAL          := $(NODE_BIN)/cz
GIT_CZ_LOCAL      := $(NODE_BIN)/git-cz
COMMITLINT_LOCAL  := $(NODE_BIN)/commitlint

# --- Конфигурация пакетов для npm exec (авто-подтягивание последних версий) ---
NPMX                 ?= npm exec --yes
CZ_PKG               ?= cz-conventional-changelog@latest   # предоставляет бинарь `git-cz`
COMMITLINT_PKGS      ?= @commitlint/cli@latest @commitlint/config-conventional@latest

# Диапазон для lint (по умолчанию — последний коммит)
FROM ?= HEAD~1
TO   ?= HEAD

# --- Проверки окружения --------------------------------------------------------
.PHONY: check-root check-dirs
check-root:
	# Запускать из корня репозитория — гарантирует корректные пути
	if [[ "$$(pwd)" != "$(ROOT_DIR)" ]]; then
	  echo "❌ Запустите make из корня репозитория: $(ROOT_DIR)"; exit 1; fi

check-dirs:
	mkdir -p "$(COMMITS_DIR)"

# --- Команды -------------------------------------------------------------------
.PHONY: commit setup-commits lint-commits

## Запустить интерактивный мастер Commitizen (git-cz). Без локальной установки — через npm exec.
commit: check-root check-dirs
	cd "$(COMMITS_DIR)"; \
	# Предпочитаем локальные бинарники, если вдруг уже установлены.
	if [[ -x "$(GIT_CZ_LOCAL)" ]]; then \
	  CMD='$(GIT_CZ_LOCAL)'; \
	elif [[ -x "$(CZ_LOCAL)" ]]; then \
	  CMD='$(CZ_LOCAL) --hook'; \
	else \
	  # Без локальных deps — берём последнюю версию адаптера и его бинарь `git-cz`
	  CMD='$(NPMX) --package=$(CZ_PKG) git-cz'; \
	fi; \
	echo "▶ запускаю: $$CMD"; \
	$$CMD || { status=$$?; \
	  if [[ $$status -eq 130 ]]; then echo "🚪 Коммит отменён пользователем (Ctrl+C)."; exit 130; fi; \
	  echo "⚠️  Ошибка мастера коммитов. Ставлю хуки и пробую ещё раз…"; \
	  $(MAKE) -C "$(ROOT_DIR)" setup-commits; \
	  $$CMD; \
	}

## Установить git-хуки (prepare-commit-msg, commit-msg)
setup-commits: check-root check-dirs
	cd "$(COMMITS_DIR)"; \
	command -v pre-commit >/dev/null || { \
	  echo "❌ Требуется pre-commit (pipx install pre-commit | pip install --user pre-commit)"; exit 1; }; \
	pre-commit install --install-hooks \
	  $(foreach h,$(COMMIT_HOOK_TYPES), --hook-type $(h)); \
	echo "✅ Хуки установлены: $(COMMIT_HOOK_TYPES)"

## Провалидировать коммиты (по умолчанию — последний: FROM=$(FROM) TO=$(TO))
lint-commits: check-root check-dirs
	cd "$(COMMITS_DIR)"; \
	if [[ -x "$(COMMITLINT_LOCAL)" ]]; then \
	  CL='$(COMMITLINT_LOCAL)'; \
	else \
	  # Без локальных deps — тянем свежие версии commitlint и пресета
	  CL='$(NPMX) $(foreach p,$(COMMITLINT_PKGS),--package=$(p)) commitlint'; \
	fi; \
	echo "▶ запускаю: $$CL --config $(COMMITLINT_CONFIG) --from $(FROM) --to $(TO)"; \
	$$CL --config "$(COMMITLINT_CONFIG)" \
	     --from "$(FROM)" --to "$(TO)" --color --verbose; \
	echo "✅ commitlint: диапазон $(FROM)..$(TO) проверен"
