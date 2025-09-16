// Semantic Release configuration
// Docs:
//   - https://semantic-release.gitbook.io/semantic-release/
//   - Conventional Commits: https://www.conventionalcommits.org/
//
// Назначение этого конфига:
//   - Выпуск релизов из стабильной ветки `main` (теги вида v1.2.3).
//   - Поддержка maintenance-веток (например, 1.2.x).
//   - Предварительные релизы из `develop` (канал "beta": v1.2.3-beta.1).
//   - Генерация CHANGELOG.md, коммит изменений и публикация релиза на GitHub.
//
// Требуемые секреты (в CI):
//   - GITHUB_TOKEN (или GH_TOKEN) с правами на push и выпуск релизов.
//
// Запуск локально (без публикации):
//   npx semantic-release --dry-run --no-ci
//
// Подсказка по коммитам (Conventional Commits):
//   feat(scope): описание — MINOR
//   fix(scope): описание — PATCH
//   perf/build/revert — тоже PATCH (см. releaseRules)
//   BREAKING CHANGE: ... — MAJOR (в body/footers)
//   docs/chore/ci/style/test — релиз не создают (см. ниже)

/** @type {import('semantic-release').Options} */
module.exports = {
    // --- Ветки и каналы -------------------------------------------------------
    //
    // ВНИМАНИЕ: свойство tagFormat задаётся ГЛОБАЛЬНО (см. ниже).
    // В объекте ветки нельзя задавать tagFormat — semantic-release его игнорирует.
    //
    branches: [
        // Maintenance ветки: 1.2.x, 2.x, 3.4.x и т.п.
        '+([0-9])?(.{+([0-9]),x}).x',
        // Стабильная ветка
        'main',
        // Предрелизная ветка: релиз идёт в канал "beta" с версиями vX.Y.Z-beta.N
        { name: 'develop', channel: 'beta', prerelease: 'beta' },
        // (Опционально) дополнительный канал для release candidates:
        // { name: 'next', channel: 'next', prerelease: 'rc' },
    ],

    // Глобальный формат тега релиза
    tagFormat: 'v${version}',

    // Базовый пресет: Conventional Commits
    preset: 'conventionalcommits',

    // --- Плагины --------------------------------------------------------------
    // Порядок важен:
    // 1) commit-analyzer — определяет тип релиза (major/minor/patch/skip)
    // 2) release-notes-generator — готовит release notes по коммитам
    // 3) changelog — пишет/обновляет CHANGELOG.md
    // 4) git — коммитит CHANGELOG.md и другие артефакты
    // 5) github — создаёт GitHub Release (и прикрепляет release notes)
    //
    // Дополнительно можно добавить:
    // - @semantic-release/exec (скрипты до/после релиза),
    // - @semantic-release/npm (публикация в npm), и т.п.
    plugins: [
        // 0) Быстрая валидация окружения/доступов
        [
            '@semantic-release/exec',
            {
                // Эти команды выполняются только для проверки окружения.
                // Ничего критичного: если не хотите — удалите весь плагин exec.
                // 'verifyConditionsCmd': 'node -e "process.exit(0)"'
            },
        ],

        // 1) Анализ коммитов — решает, будет ли релиз и какой.
        [
            '@semantic-release/commit-analyzer',
            {
                preset: 'conventionalcommits',
                releaseRules: [
                    // Дополнительные правила к дефолтным из conventionalcommits
                    { type: 'perf', release: 'patch' },
                    { type: 'build', release: 'patch' },
                    { type: 'revert', release: 'patch' },
                    // Шумовые типы — не инициируют релиз
                    { type: 'ci', release: false },
                    { type: 'chore', release: false },
                    { type: 'style', release: false },
                    { type: 'test', release: false },
                    // docs и refactor по умолчанию не релизят (оставляем дефолт)
                ],
            },
        ],

        // 2) Генерация release notes (для GitHub Release и CHANGELOG)
        [
            '@semantic-release/release-notes-generator',
            {
                preset: 'conventionalcommits',
                presetConfig: {
                    // Отображаемые секции в релиз-нотах/CHANGELOG
                    types: [
                        { type: 'feat', section: 'Features' },
                        { type: 'fix', section: 'Bug Fixes' },
                        { type: 'perf', section: 'Performance' },
                        { type: 'docs', section: 'Documentation' },
                        { type: 'refactor', section: 'Refactoring' },
                        { type: 'revert', section: 'Reverts' },
                        // Скрываем шум
                        { type: 'test', section: 'Tests', hidden: true },
                        { type: 'style', section: 'Style', hidden: true },
                        { type: 'build', section: 'Build System', hidden: true },
                        { type: 'ci', section: 'CI', hidden: true },
                        { type: 'chore', section: 'Misc', hidden: true },
                    ],
                },
            },
        ],

        // 3) Обновление CHANGELOG.md
        [
            '@semantic-release/changelog',
            {
                changelogFile: 'CHANGELOG.md',
            },
        ],

        // 4) Коммит обновлённого CHANGELOG.md (и других файлов, если надо)
        [
            '@semantic-release/git',
            {
                assets: [
                    'CHANGELOG.md',
                    // Добавьте сюда другие артефакты, которые хотите закоммитить:
                    // 'docs/**',
                    // 'packages/*/CHANGELOG.md',
                ],
                message:
                    'chore(release): ${nextRelease.version}\n\n${nextRelease.notes}\n\n[skip ci]',
            },
        ],

        // 5) Публикация релиза в GitHub
        '@semantic-release/github',
    ],

    // Не падать с ошибкой, если изменений нет (например, только chore/docs)
    failOnEmptyRelease: false,

    // Запуск в CI: semantic-release сам определяет CI, флаг оставляем явным
    ci: true,

    // Сухой прогон (по умолчанию выкл). Включайте локально через CLI.
    dryRun: false,

    // Дополнительная отладка (выводит больше логов)
    debug: false,
};
