#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор паролей по «памятке-алгоритму» (пул S*, перец W, вплетение).

ВАЖНО: Алгоритм НЕ изменён по сравнению с исходником; обновлены только стиль кода,
структура и комментарии в духе современного Python (PEP 8/257).

Безопасность:
  - Секреты (пул S* и «перец» W) рекомендуется вводить интерактивно через флаги
    --ask-sstar-pool / --ask-s0-pool и --pepper-ask.
  - Аргументы командной строки и переменные окружения считаются менее безопасными.

Примеры запуска смотрите в README_passgen_pool.md.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from getpass import getpass
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Константы и настройки
# ---------------------------------------------------------------------------

# Последовательности по умолчанию для построения S* (Q) и символа SYM (P).
Q_DEFAULT: str = "!@#$%^&*+?"
P_DEFAULT: str = "!@#$%^&*+?"

# Имена переменных окружения.
ENV_Q_SEQ = "PASSGEN_Q_SEQ"
ENV_P_SEQ = "PASSGEN_P_SEQ"
ENV_SSTAR_POOL = "PASSGEN_SSTAR_POOL"
ENV_PEPPER = "PASSGEN_PEPPER"

# Коды возврата (для единообразия).
EX_USAGE = 2           # Некорректное использование/аргументы
EX_INTERRUPT = 130     # Прерывание пользователем (Ctrl+C)


# ---------------------------------------------------------------------------
# Вспомогательные функции (алгоритм НЕ меняем)
# ---------------------------------------------------------------------------

def only_letters(s: str) -> str:
    """Возвращает только латинские буквы a-z в нижнем регистре."""
    return re.sub(r"[^a-z]", "", s.lower())


def is_letter(ch: str) -> bool:
    """Проверяет, является ли символ латинской буквой (A–Z или a–z)."""
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z")


def is_upper(ch: str) -> bool:
    """Проверяет, является ли символ заглавной латинской буквой."""
    return "A" <= ch <= "Z"


def sum_letter_positions(s: str) -> int:
    """
    Возвращает сумму позиций букв (a=1..z=26). Небуквенные символы игнорируются.
    """
    total = 0
    for ch in s.lower():
        if "a" <= ch <= "z":
            total += ord(ch) - 96
    return total


def sum_digits(s: str) -> int:
    """Суммирует все цифры в строке."""
    return sum(int(c) for c in s if c.isdigit())


def capitalize_1_3(s: str) -> str:
    """
    Делает заглавными 1‑ю и 3‑ю буквы (если есть), остальные буквы — строчные.
    Небуквенные символы не меняются.
    """
    out: list[str] = []
    for i, ch in enumerate(s):
        if i in (0, 2) and ch.isalpha():
            out.append(ch.upper())
        else:
            out.append(ch.lower() if ch.isalpha() else ch)
    return "".join(out)


def site_key(domain: str) -> str:
    """
    Возвращает ключ K: домен без поддоменов/зоны (gmail.com -> gmail; yandex.ru -> yandex).
    """
    d = domain.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = d.split("/")[0]
    parts = d.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return parts[0]


def tag4_from_key(k: str) -> str:
    """
    Возвращает T: первые 2 + последние 2 буквы из ключа K (только латиница; добивка 'x').
    """
    letters = only_letters(k)
    if len(letters) >= 4:
        return letters[:2] + letters[-2:]
    return (letters + "xxxx")[:4]


def u4_from_login(login: str) -> str:
    """
    Возвращает U: из логина до @, только буквы, первые 2 + последние 2 (добивка 'x').
    """
    loc = login.split("@")[0]
    letters = only_letters(loc)
    if len(letters) >= 4:
        return letters[:2] + letters[-2:]
    return (letters + "xxxx")[:4]


def l2_from_key(k: str) -> str:
    """Возвращает L2: длина K mod 100, строка из двух цифр с ведущим нулём."""
    return f"{len(k) % 100:02d}"


def build_strengthened_base(s0: str, q_seq: list[str]) -> str:
    """
    Строит усиленную базу S* из S0 по правилу:
      - идём слева направо;
      - перед БУКВОЙ вставляем следующий символ из Q, если слева не буква или сменился регистр;
      - перед цифрой/прочим символом ничего не вставляем;
      - если подряд идут буквы одного регистра — перед второй/следующими не вставляем.
    """
    out: list[str] = []
    qi = 0
    prev = ""
    for ch in s0:
        if is_letter(ch):
            if not is_letter(prev) or (is_upper(prev) != is_upper(ch)):
                out.append(q_seq[qi % len(q_seq)])
                qi += 1
            out.append(ch)
        else:
            out.append(ch)
        prev = ch
    return "".join(out)


def compute_sym(
    T: str, U: str, year_full: str, p_seq: list[str], r_shift: int
) -> tuple[str, int, int]:
    """
    Считает:
      - sumT = Σpos(T), sumU = Σpos(U), sy = Σdigits(год);
      - idx = (sumT + sumU + sy + r_shift) mod 10;
      - SYM = P[idx].
    Возвращает кортеж (SYM, idx, sy).
    """
    sumT = sum_letter_positions(T)
    sumU = sum_letter_positions(U)
    sy = sum_digits(year_full)
    idx = (sumT + sumU + sy + r_shift) % 10
    return p_seq[idx], idx, sy


def choose_pool_index(
    Kletters: str, Uletters: str, r_shift: int, pool_size: int
) -> int:
    """
    Выбирает индекс S* из пула по формуле:
      i = (Σpos(Kletters) + Σpos(Uletters) + r_shift) mod N.
    """
    SK = sum_letter_positions(Kletters)
    SU = sum_letter_positions(Uletters)
    return (SK + SU + r_shift) % pool_size


def cut_sstar_for_interleave(sstar: str, idx: int, syear: int) -> tuple[str, str, str]:
    """
    Режет S* на S1,S2,S3:
      d1 = (idx % 4) + 2  →  2..5
      d2 = (syear % 3) + 2 →  2..4
    """
    d1 = (idx % 4) + 2
    d2 = (syear % 3) + 2
    s1 = sstar[:d1]
    s2 = sstar[d1 : d1 + d2]
    s3 = sstar[d1 + d2 :]
    return s1, s2, s3


def assemble_interleaved(
    sstar: str, sym: str, Tcap: str, L2: str, Y2: str, Ucap: str, idx: int, syear: int
) -> str:
    """Возвращает пароль по формуле: SYM + S1 + T^ + S2 + L2 + S3 + Y2 + U^"""
    S1, S2, S3 = cut_sstar_for_interleave(sstar, idx, syear)
    return f"{sym}{S1}{Tcap}{S2}{L2}{S3}{Y2}{Ucap}"


def assemble_classic(sstar: str, sym: str, Tcap: str, L2: str, Y2: str, Ucap: str) -> str:
    """Возвращает пароль по формуле: S* + SYM + T^ + L2 + Y2 + U^"""
    return f"{sstar}{sym}{Tcap}{L2}{Y2}{Ucap}"


def ask_pool_sstar(n: int, prompt_label: str) -> list[str]:
    """Запрашивает у пользователя n строк S* (без эха)."""
    pool: list[str] = []
    for i in range(n):
        while True:
            s = getpass(f"{prompt_label} S*[{i}] (минимум 10 символов): ")
            if len(s) >= 10:
                pool.append(s)
                break
            print("Слишком короткая S*. Повторите (≥10).", file=sys.stderr)
    return pool


def ask_pool_s0_and_build(n: int, q_seq: list[str]) -> list[str]:
    """Запрашивает у пользователя n строк S0 и строит для них S* по правилу Q."""
    pool: list[str] = []
    for i in range(n):
        while True:
            s0 = getpass("Введите S0[{i}] (исходная база, будет преобразована в S*): ".format(i=i))
            if len(s0) >= 6:
                sstar = build_strengthened_base(s0, q_seq=q_seq)
                pool.append(sstar)
                break
            print("Слишком короткая S0. Повторите (≥6).", file=sys.stderr)
    return pool


def pepper_to_shift(pepper_word: str, pool_size: int) -> int:
    """Переводит слово‑перец W в сдвиг r = Σpos(W) mod N."""
    return sum_letter_positions(pepper_word) % pool_size


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Генератор паролей: пул S*, перец W, вплетение S*.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--login", required=True, help="Логин (email или локальная часть)")
    parser.add_argument("--domain", required=True, help="Домен сайта (пример: yandex.ru)")
    parser.add_argument("--year", required=True, help="Год или версия (например: 2005 или 25)")
    parser.add_argument("--classic", action="store_true", help="Классическая сборка без вплетения")
    parser.add_argument("--pool-size", type=int, default=4, help="Размер пула S* (3..8)")
    parser.add_argument(
        "--ask-sstar-pool",
        action="store_true",
        help="Безопасно ввести пул S* (каждая без преобразования)",
    )
    parser.add_argument(
        "--ask-s0-pool",
        action="store_true",
        help="Безопасно ввести пул S0 и построить S* по Q",
    )
    parser.add_argument(
        "--sstar-pool",
        help="НЕБЕЗОПАСНО: задать пул S* через ';' (пример: 'A;B;C')",
    )
    parser.add_argument(
        "--pepper-ask", action="store_true", help="Безопасно ввести слово‑перец W (для расчёта r)"
    )
    parser.add_argument("--pepper", help="НЕБЕЗОПАСНО: задать перец W напрямую (строка)")
    parser.add_argument("--q-seq", help=f"Последовательность Q для S* (по умолчанию {Q_DEFAULT!r})")
    parser.add_argument("--p-seq", help=f"Последовательность P для SYM (по умолчанию {P_DEFAULT!r})")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Точка входа. Возвращает код завершения процесса."""
    args = parse_args(argv)

    if not (3 <= args.pool_size <= 8):
        print("pool-size должен быть в пределах 3..8.", file=sys.stderr)
        return EX_USAGE

    # Последовательности Q/P: сначала переменные окружения, затем аргументы, затем дефолты.
    q_seq = list(os.getenv(ENV_Q_SEQ) or args.q_seq or Q_DEFAULT)
    p_seq = list(os.getenv(ENV_P_SEQ) or args.p_seq or P_DEFAULT)

    # Год / версия
    year_full = args.year.strip()
    if not re.fullmatch(r"\d{2,4}", year_full):
        print("Параметр --year должен быть числом (2–4 цифры), например 05 или 2005.", file=sys.stderr)
        return EX_USAGE
    Y2 = year_full[-2:]
    syear = sum_digits(year_full)  # сумма цифр для d2 и SYM

    # K, T, U и формы ^
    K = site_key(args.domain)
    Kletters = only_letters(K)  # важно для индекса пула
    T = tag4_from_key(K)
    Tcap = capitalize_1_3(T)
    L2 = l2_from_key(K)

    U = u4_from_login(args.login)
    Ucap = capitalize_1_3(U)
    Uletters_full = only_letters(args.login.split("@")[0])  # для индекса пула

    # Получаем пул S*
    pool: List[str] = []
    if args.ask_sstar_pool:
        pool = ask_pool_sstar(args.pool_size, "Введите")
    elif args.ask_s0_pool:
        pool = ask_pool_s0_and_build(args.pool_size, q_seq=q_seq)
    elif args.sstar_pool:
        # небезопасно: из аргумента командной строки
        pool = [s for s in args.sstar_pool.split(";") if s]
    else:
        # можно использовать переменную окружения (небезопасно)
        env_pool = os.getenv(ENV_SSTAR_POOL, "")
        if env_pool:
            pool = [s for s in env_pool.split(";") if s]
        else:
            print(
                "Не задан пул S*. Укажите --ask-sstar-pool или --ask-s0-пool (рекомендуется).",
                file=sys.stderr,
            )
            return EX_USAGE

    if len(pool) < args.pool_size:
        print(f"В пуле должно быть {args.pool_size} основ S*, сейчас {len(pool)}.", file=sys.stderr)
        return EX_USAGE

    # Получаем «перец» W -> сдвиг r
    if args.pepper_ask:
        pepper = getpass("Введите слово‑перец W (только для вас): ")
        if not pepper:
            print("Пустой перец W не допускается.", file=sys.stderr)
            return EX_USAGE
    elif args.pepper:
        pepper = args.pepper
    else:
        pepper = os.getenv(ENV_PEPPER, "")
        if not pepper:
            print(
                "Не задан перец W. Укажите --pepper-ask (рекомендуется) или переменную PASSGEN_PEPPER.",
                file=sys.stderr,
            )
            return EX_USAGE

    r_shift = pepper_to_shift(pepper, args.pool_size)

    # Выбор индекса S* из пула
    i = choose_pool_index(Kletters, Uletters_full, r_shift, args.pool_size)
    sstar = pool[i]

    # Символ SYM (с учётом r)
    sym, idx, _ = compute_sym(T, U, year_full, p_seq=p_seq, r_shift=r_shift)

    # Сборка
    if args.classic:
        password = assemble_classic(sstar, sym, Tcap, L2, Y2, Ucap)
    else:
        password = assemble_interleaved(sstar, sym, Tcap, L2, Y2, Ucap, idx, syear)

    print(password)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.", file=sys.stderr)
        raise SystemExit(EX_INTERRUPT)
