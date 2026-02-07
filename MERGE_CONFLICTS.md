# Как быстро решить merge conflict в этом проекте

Если GitHub пишет, что конфликт в `README.md` и `main.py`, сделай так локально:

```bash
# 1) получить свежие изменения
git fetch origin

# 2) перейти на свою ветку с PR
git checkout <your-branch>

# 3) подтянуть целевую ветку (обычно main)
git merge origin/main
# или git rebase origin/main
```

Дальше открыть конфликтующие файлы и убрать маркеры:

- `<<<<<<< HEAD`
- `=======`
- `>>>>>>> ...`

После ручного объединения:

```bash
git add README.md main.py

# если был merge
git commit -m "Resolve merge conflicts in README and main game loop"

# если был rebase
git rebase --continue

# отправка
# merge-ветка:
git push
# rebase-ветка:
git push --force-with-lease
```

## Что лучше оставить из нашей версии

- в `main.py`: лечение на `E` (без конфликта с движением `W`), визуальные эффекты `Q`/лечения/попаданий;
- в `README.md`: актуальные кнопки (`Q`, `E`, `WASD`) и описание визуальных эффектов.

## Быстрая проверка после разрешения

```bash
python3 -m py_compile main.py
python3 main.py
```
