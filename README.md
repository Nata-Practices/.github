# Инструкция: Как залить проект в GitHub через JetBrains IDE с использованием Git Remotes

## 🛠️ Предварительные настройки
Перед началом убедитесь, что выполнены следующие шаги:
1. **Установлен Git**: Убедитесь, что Git установлен на компьютере. [Скачать Git](https://git-scm.com/downloads).
2. **Создан репозиторий на GitHub**:
   - Зайди на [GitHub](https://github.com/Nata-Practices) и создай новый **ПРИВАТНЫЙ** репозиторий.
   - Скопируй URL твоего репозитория (например, `https://github.com/Nata-Practices/repository.git`).

---

## 🚀 Шаги для загрузки проекта в GitHub

### 1. Открытие проекта
Открой твой проект в JetBrains IDE (например, IntelliJ IDEA, Android Studio, PyCharm и т.д.).

---

### 2. Инициализация Git-репозитория (если не сделано)
Если в проекте ещё нет репозитория Git:
1. Перейди в верхнее меню (в левом верхнем углу) **VCS** → **Enable Version Control Integration**.
2. В открывшемся окне выбери `Git` и нажми **OK**.
3. Git-репозиторий будет создан локально в корне проекта.

---

### 3. Добавление удалённого репозитория (Git Remote)
1. Через верхнее меню (в левом верхнем углу) перейди в **Git** → **Manage Remotes**.
2. В открывшемся окне нажми **+** для добавления нового удалённого репозитория.
3. Вставь URL твоего репозитория (например, `https://github.com/Nata-Practices/repository.git`) и нажми **OK**.

---

### 4. Добавление файлов и коммит изменений
1. Выбери файлы, которые хочешь загрузить, в разделе **Version Control**.
2. Нажми **Commit and Push**:
   - Введи сообщение к коммиту (например, `Initial commit`).
   - Нажми **Commit and Push** что бы сразу загрузить изменения.

---

### 5. Проверка изменений на GitHub
1. Зайди в репозиторий на [GitHub](https://github.com/Nata-Practices).
2. Убедись, что все изменения успешно загружены.

---

## 💡 Советы
- **Игнорирование файлов**: Чтобы исключить лишние файлы (например, `node_modules`, `.idea`, `.gradle`, или `build`), добавь их в файл `.gitignore`. Этот файл можно создать в корне проекта, либо использовать генератор .gitignore из плагина в JetBrains.
- **Описание проекта (README)**: Убедись, что в корне проекта есть файл `readme.md`. Этот файл помогает другим разработчикам (и тебе самому) понять, что делает проект и как его использовать. Пример содержания `readme.md`:
  ```markdown
  # Название проекта

  ## 📖 Описание
  Краткое описание проекта, его цели и назначения.

  (если это необходимо и есть какие-то непонтятки с этим)
  ## 🛠️ Установка
  1. Склонируйте репозиторий:
     git clone https://github.com/Nata-Practices/repository.git

  2. Следуйте инструкциям для запуска проекта.

  ## 🚀 Основной функционал
  - Функция 1
  - Функция 2
  - Функция 3

  ## 📚 Используемые технологии
  - Kotlin/Java
  - Gradle
  - И т.д.
  ```
- **Управление конфликтами**: Если ты столкнулась с конфликтами при `Pull` или `Push`, JetBrains предложит визуальный интерфейс для их разрешения.
- **Тип коммитов**
  - feat - используется при добавлении новой функциональности.
  - fix - исправление багов.
  - refactor - изменения кода, которые не исправляет баги и не добавляют функционал.
  - chore - изменение конфигов, системы сборки, обновление зависимостей и т.д.
  - test - всё, что связано с тестированием.
  - style - исправление опечаток, изменение форматирования кода (переносы, отступы, точки с запятой и т.п.) без изменения смысла кода.
  - docs - изменения только в документации.

---

## 📚 Полезные команды Git
Если хочешь использовать терминал внутри IDE, либо cmd, вот некоторые полезные команды:
```bash
# Инициализация репозитория
git init

# Добавление удалённого репозитория
git remote add origin <URL>

# Добавление всех файлов в индекс
git add .

# Создание коммита
git commit -m "Initial commit"

# Отправка изменений
git push -u origin master

# Очистка игнорируемых файлов (после изменения .gitignore)
git rm -r --cached .
git add .
git commit -m "refactor: Remove ignored files"
git push
```

Теперь твой проект успешно загружен на GitHub через JetBrains IDE! 🎉
