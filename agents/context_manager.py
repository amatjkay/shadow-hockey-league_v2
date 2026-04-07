"""
Context Manager - Управление контекстом системы агентов

Отвечает за чтение, запись и суммаризацию файлов в context/
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ContextData:
    """Структура данных контекста."""
    state_summary: str = ""
    active_plan: str = ""
    architecture: str = ""
    qa_status: str = ""
    design_specs: str = ""
    deployment_issues: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class ContextManager:
    """
    Менеджер контекста для системы агентов.
    
    Управляет чтением/записью файлов в context/,
    обеспечивает безопасность (редатктирование секретов)
    и автосуммаризацию при превышении лимитов.
    """

    # Лимит токенов (приблизительно 1 токен = 4 символа)
    TOKEN_LIMIT = 100000
    CHARS_PER_TOKEN = 4
    
    def __init__(self, context_dir: Optional[str] = None):
        """
        Инициализация менеджера контекста.
        
        Args:
            context_dir: Путь к директории context/ (по умолчанию: project_root/context/)
        """
        if context_dir:
            self.context_dir = Path(context_dir)
        else:
            # По умолчанию: project_root/context/
            self.context_dir = Path(__file__).parent.parent / "context"
        
        # Создаём директорию если не существует
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ContextManager initialized: {self.context_dir}")

    def load_state_summary(self) -> str:
        """Загрузить сводку состояния из state_summary.md."""
        return self._read_file("state_summary.md")

    def load_active_plan(self) -> str:
        """Загрузить активный план из active_plan.md."""
        return self._read_file("active_plan.md")

    def load_architecture(self) -> str:
        """Загрузить архитектуру из architecture.md."""
        return self._read_file("architecture.md")

    def load_qa_status(self) -> str:
        """Загрузить статус QA из qa_status.md."""
        return self._read_file("qa_status.md")

    def load_design_specs(self) -> str:
        """Загрузить спецификации дизайна из design_specs.md."""
        return self._read_file("design_specs.md")

    def load_deployment_issues(self) -> str:
        """Загрузить проблемы деплоя из deployment_issues.md."""
        return self._read_file("deployment_issues.md")

    def load_all(self) -> ContextData:
        """Загрузить весь контекст."""
        return ContextData(
            state_summary=self.load_state_summary(),
            active_plan=self.load_active_plan(),
            architecture=self.load_architecture(),
            qa_status=self.load_qa_status(),
            design_specs=self.load_design_specs(),
            deployment_issues=self.load_deployment_issues(),
            last_updated=datetime.now().isoformat()
        )

    def save_state_summary(self, content: str):
        """Сохранить сводку состояния."""
        self._write_file("state_summary.md", content)

    def save_active_plan(self, content: str):
        """Сохранить активный план."""
        self._write_file("active_plan.md", content)

    def save_architecture(self, content: str):
        """Сохранить архитектуру."""
        self._write_file("architecture.md", content)

    def save_qa_status(self, content: str):
        """Сохранить статус QA."""
        self._write_file("qa_status.md", content)

    def save_design_specs(self, content: str):
        """Сохранить спецификации дизайна."""
        self._write_file("design_specs.md", content)

    def save_deployment_issues(self, content: str):
        """Сохранить проблемы деплоя."""
        self._write_file("deployment_issues.md", content)

    def save_artifacts(self, role_name: str, artifacts: Dict[str, Any]):
        """
        Сохранить артефакты от агента.
        
        Args:
            role_name: Имя роли (ANALYST, DEVELOPER, etc.)
            artifacts: Словарь с артефактами
        """
        artifacts_dir = self.context_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{role_name.lower()}_{timestamp}.json"
        
        # Редаттируем секреты перед сохранением
        safe_artifacts = self._redact_secrets(artifacts)
        
        filepath = artifacts_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(safe_artifacts, f, indent=2, ensure_ascii=False)
            logger.info(f"Artifacts saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save artifacts: {e}")

    def estimate_token_count(self, text: str) -> int:
        """
        Приблизительная оценка количества токенов.
        
        Args:
            text: Текст для оценки
            
        Returns:
            Примерное количество токенов
        """
        return len(text) // self.CHARS_PER_TOKEN

    def needs_summarization(self, context: ContextData) -> bool:
        """
        Проверить, нужна ли суммаризация контекста.
        
        Args:
            context: Данные контекста
            
        Returns:
            True если превышен лимит токенов
        """
        total_text = (
            context.state_summary +
            context.active_plan +
            context.architecture +
            context.qa_status +
            context.design_specs +
            context.deployment_issues
        )
        
        token_count = self.estimate_token_count(total_text)
        return token_count > self.TOKEN_LIMIT

    def create_summary(self, context: ContextData, summary: str):
        """
        Создать суммаризированный контекст.
        
        Args:
            context: Исходные данные контекста
            summary: Суммаризированная версия
        """
        # Сохраняем старый контекст как архив
        self._archive_context()
        
        # Записываем новую суммаризацию
        self.save_state_summary(summary)
        
        logger.info("Context summarized and archived")

    def _archive_context(self):
        """Архивировать текущий контекст."""
        archive_dir = self.context_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_subdir = archive_dir / timestamp
        archive_subdir.mkdir(exist_ok=True)
        
        # Копируем все .md файлы
        for md_file in self.context_dir.glob("*.md"):
            dest = archive_subdir / md_file.name
            try:
                dest.write_text(md_file.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to archive {md_file}: {e}")
        
        logger.info(f"Context archived to {archive_subdir}")

    def _read_file(self, filename: str) -> str:
        """
        Прочитать файл из context/.
        
        Args:
            filename: Имя файла
            
        Returns:
            Содержимое файла или пустая строка
        """
        filepath = self.context_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Context file not found: {filepath}")
            return ""
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            logger.debug(f"Read {len(content)} chars from {filepath}")
            return content
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return ""

    def _write_file(self, filename: str, content: str):
        """
        Записать файл в context/.
        
        Args:
            filename: Имя файла
            content: Содержимое
        """
        filepath = self.context_dir / filename
        
        # Редаттируем секреты перед записью
        safe_content = self._redact_secrets(content)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(safe_content)
            logger.info(f"Written {len(safe_content)} chars to {filepath}")
        except Exception as e:
            logger.error(f"Failed to write {filepath}: {e}")

    def _redact_secrets(self, data: Any) -> Any:
        """
        Заменить секреты на [REDACTED].
        
        Args:
            data: Данные для обработки (str, dict, list)
            
        Returns:
            Безопасные данные
        """
        # Паттерны для поиска секретов
        secret_patterns = [
            r'(password|passwd|pwd)\s*[:=]\s*\S+',
            r'(api_key|apikey|api_token)\s*[:=]\s*\S+',
            r'(secret|secret_key)\s*[:=]\s*\S+',
            r'(token|access_token)\s*[:=]\s*\S+',
            r'(aws_access_key|aws_secret_key)\s*[:=]\s*\S+',
            r'-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----',
        ]
        
        if isinstance(data, str):
            result = data
            for pattern in secret_patterns:
                result = re.sub(pattern, r'\1: [REDACTED]', result, flags=re.IGNORECASE)
            return result
        
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Пропускаем ключи которые выглядят как секреты
                if any(s in key.lower() for s in ['password', 'secret', 'token', 'key', 'credential']):
                    result[key] = '[REDACTED]'
                else:
                    result[key] = self._redact_secrets(value)
            return result
        
        elif isinstance(data, list):
            return [self._redact_secrets(item) for item in data]
        
        return data

    def get_context_size(self) -> Dict[str, int]:
        """
        Получить размер контекста в токенах.
        
        Returns:
            Словарь с размерами файлов
        """
        sizes = {}
        total_chars = 0
        
        for md_file in self.context_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                char_count = len(content)
                total_chars += char_count
                sizes[md_file.name] = {
                    "chars": char_count,
                    "tokens": char_count // self.CHARS_PER_TOKEN
                }
            except Exception:
                pass
        
        sizes["total"] = {
            "chars": total_chars,
            "tokens": total_chars // self.CHARS_PER_TOKEN
        }
        
        return sizes
