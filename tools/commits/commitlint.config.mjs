// Commitlint-конфигурация для проверки сообщений коммитов по Conventional Commits 1.0.0.
//
// Цели
// - Единый строгий формат истории для автогенерации CHANGELOG и семантических версий.
// - Предсказуемые BREAKING-изменения (только через футер `BREAKING CHANGE:`).
// - Обязательный scope для удобной навигации в моно/мульти-репозиториях.
//
// Политика
// - Требуется: <type>(<scope>): <subject>
// - scope обязателен и оформляется в kebab-case (пример: auth-api).
// - Заголовок <= 100 символов; в теме нет завершающей точки и восклицательного знака.
// - Тело/футер, если есть, отделяются пустой строкой; длина строк ограничена.
//
// Совместимость
// - База: официальный пресет `@commitlint/config-conventional` (структура и набор типов).
// - Совместимо с инструментами, использующими Conventional Commits:
//   semantic-release, release-please, semantic-pull-request.
//
// Документация
// - Conventional Commits 1.0.0: https://www.conventionalcommits.org
// - Правила commitlint: https://commitlint.js.org/reference/rules.html
/** @type {import('@commitlint/types').UserConfig} */
export default {
    // Наследуем официальный пресет (типы, парсер, базовые правила)
    extends: ['@commitlint/config-conventional'],

    // Усиленные правила формата и читаемости
    rules: {
        // --- Структура заголовка ---
        'type-empty': [2, 'never'],                 // тип обязателен
        'type-case': [2, 'always', 'lower-case'],   // тип в нижнем регистре

        'scope-empty': [2, 'never'],                // scope обязателен
        'scope-case': [2, 'always', 'kebab-case'],  // scope в kebab-case

        'subject-empty': [2, 'never'],              // тема обязательна
        'subject-full-stop': [2, 'never', '.'],     // без точки в конце
        'subject-exclamation-mark': [2, 'never'],   // без '!' в заголовке (BR по футеру)
        'subject-case': [2, 'never', [              // запрет «капитализированных» форм
            'sentence-case', 'start-case', 'pascal-case', 'upper-case'
        ]],

        // --- Длина и читабельность ---
        'header-max-length': [2, 'always', 100],        // предел для заголовка
        'body-max-line-length': [2, 'always', 100],     // предел длины строки в теле (если есть)
        'footer-max-line-length': [2, 'always', 100],   // предел длины строки в футере (если есть)

        // --- Отделение блоков ---
        'body-leading-blank': [2, 'always'],    // пустая строка перед телом
        'footer-leading-blank': [2, 'always']   // пустая строка перед футером
    }
};
