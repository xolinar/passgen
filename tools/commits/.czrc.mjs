// Commitizen: конфигурация адаптера `cz-conventional-changelog`
// Назначение
//   - Интерактивная сборка сообщений коммитов в формате Conventional Commits 1.0.0.
//   - Дружит с commitlint и релиз-ботами (semantic-release / release-please).
//
// Принципы
//   - Строгий формат: <type>(<scope>): <subject>  (+ опциональные body/footer).
//   - `scope` обязателен и должен быть в kebab-case.
//   - `subject` обязателен и должен быть в нижнем регистре.
//   - Заголовок ≤ 100 символов; без точки/восклицательного знака в конце темы.
//   - Перед body/footer — пустая строка.
//
// Совместимость и ссылки:
//  - Параметры адаптера: https://commitizen-tools.github.io/commitizen/
//  - Commitizen CLI: https://commitizen.github.io/cz-cli/

module.exports = {
    // Базовый адаптер Commitizen (Angular/Conventional Changelog preset)
    path: 'cz-conventional-changelog',

    // Длины (если в проекте подключён commitlint, maxHeaderWidth возьмётся из
    // правила `header-max-length`; это поведение описано в README адаптера)
    maxHeaderWidth: 100,
    maxLineWidth: 100,

    // Регистры:
    //  - scope оставляем в нижнем регистре (помогает выдержать kebab-case);
    //  - subject принудительно в нижний регистр.
    disableScopeLowerCase: false,
    disableSubjectLowerCase: false,

    // Значения по умолчанию (можно переопределять CZ_TYPE/CZ_SCOPE/CZ_SUBJECT/CZ_BODY и т.п.)
    defaultType: '',
    defaultScope: '',
    defaultSubject: '',
    defaultBody: '',
    defaultIssues: '',
};
