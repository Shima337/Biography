#!/usr/bin/env python3
"""
Автоматизированное тестирование извлечения людей
Отправляет тестовые сообщения и проверяет результаты
"""

import json
import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, get_db
from app.models import User, Session as DBSession, Person, Message
from app.service import ProcessingService


class PersonExtractionTester:
    def __init__(self):
        self.db = SessionLocal()
        self.service = ProcessingService(self.db)
        self.test_user = None
        self.test_session = None
        self.results = []
        
    def setup(self):
        """Создать тестового пользователя и сессию"""
        # Создать тестового пользователя
        self.test_user = User(
            name=f"Test User {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            locale="ru"
        )
        self.db.add(self.test_user)
        self.db.flush()
        
        # Создать тестовую сессию
        self.test_session = DBSession(user_id=self.test_user.id)
        self.db.add(self.test_session)
        self.db.commit()
        
        print(f"✓ Создан тестовый пользователь ID: {self.test_user.id}")
        print(f"✓ Создана тестовая сессия ID: {self.test_session.id}")
        
    def load_test_messages(self) -> List[Dict]:
        """Загрузить тестовые сообщения из JSON"""
        test_file = Path(__file__).parent / "test_messages.json"
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("messages", [])
    
    async def process_message(self, message_data: Dict) -> Dict:
        """Обработать одно сообщение и вернуть результаты"""
        message_text = message_data["text"]
        message_id = message_data["id"]
        
        print(f"\n📨 Обработка сообщения {message_id}...")
        print(f"   Текст: {message_text[:100]}...")
        
        # Отправить сообщение через сервис
        result = await self.service.process_message(
            session_id=self.test_session.id,
            message_text=message_text,
            extractor_version="v3",
            planner_version="v1"
        )
        
        # Получить извлеченных людей для v1 и v2, связанных с этим сообщением
        from app.models import MemoryPerson, Memory
        # Найти memories для этого сообщения
        memories = self.db.query(Memory).filter(
            Memory.source_message_id == result["message_id"]
        ).all()
        memory_ids = [m.id for m in memories] if memories else []
        
        # Получить людей через связи MemoryPerson
        if memory_ids:
            person_ids_v1 = self.db.query(MemoryPerson.person_id).join(
                Person
            ).filter(
                MemoryPerson.memory_id.in_(memory_ids),
                Person.pipeline_version == "v1"
            ).distinct().all()
            person_ids_v1 = [p[0] for p in person_ids_v1]
            
            person_ids_v2 = self.db.query(MemoryPerson.person_id).join(
                Person
            ).filter(
                MemoryPerson.memory_id.in_(memory_ids),
                Person.pipeline_version == "v2"
            ).distinct().all()
            person_ids_v2 = [p[0] for p in person_ids_v2]
            
            persons_v1 = self.db.query(Person).filter(Person.id.in_(person_ids_v1)).all() if person_ids_v1 else []
            persons_v2 = self.db.query(Person).filter(Person.id.in_(person_ids_v2)).all() if person_ids_v2 else []
        else:
            # Если нет memories, попробуем найти людей по first_seen_memory_id или просто всех для этого пользователя
            persons_v1 = self.db.query(Person).filter(
                Person.user_id == self.test_user.id,
                Person.pipeline_version == "v1"
            ).all()
            persons_v2 = self.db.query(Person).filter(
                Person.user_id == self.test_user.id,
                Person.pipeline_version == "v2"
            ).all()
        
        # Получить сообщение из БД
        message = self.db.query(Message).filter(
            Message.id == result["message_id"]
        ).first()
        
        return {
            "message_id": message_id,
            "message_text": message_text,
            "expected_persons": message_data.get("expected_persons", []),
            "notes": message_data.get("notes", ""),
            "persons_v1": [{"name": p.display_name, "type": p.type, "id": p.id} for p in persons_v1],
            "persons_v2": [{"name": p.display_name, "type": p.type, "id": p.id} for p in persons_v2],
            "message_db_id": message.id if message else None
        }
    
    def compare_persons(self, expected: List[Dict], actual: List[Dict], pipeline: str) -> Dict:
        """Сравнить ожидаемых и фактических людей"""
        expected_set = {(p["name"].lower(), p["type"]) for p in expected}
        actual_set = {(p["name"].lower(), p["type"]) for p in actual}
        
        # Правильно найденные
        correct = expected_set & actual_set
        
        # Пропущенные
        missed = expected_set - actual_set
        
        # Лишние
        extra = actual_set - expected_set
        
        # Проверка вариантов имен (если имя содержится в другом)
        variant_issues = []
        for exp in expected:
            exp_name_lower = exp["name"].lower()
            found_variant = False
            for act in actual:
                act_name_lower = act["name"].lower()
                # Проверяем, является ли одно имя вариантом другого
                if exp_name_lower != act_name_lower:
                    if exp_name_lower in act_name_lower or act_name_lower in exp_name_lower:
                        variant_issues.append({
                            "expected": exp["name"],
                            "found": act["name"],
                            "issue": "variant_name"
                        })
                        found_variant = True
                        break
            if not found_variant and (exp_name_lower, exp["type"]) not in actual_set:
                # Проверяем, может быть имя упомянуто в другом формате
                for act in actual:
                    if exp_name_lower in act["name"].lower() or act["name"].lower() in exp_name_lower:
                        variant_issues.append({
                            "expected": exp["name"],
                            "found": act["name"],
                            "issue": "possible_variant"
                        })
        
        # Метрики
        precision = len(correct) / len(actual_set) if actual_set else 0
        recall = len(correct) / len(expected_set) if expected_set else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "pipeline": pipeline,
            "expected_count": len(expected_set),
            "actual_count": len(actual_set),
            "correct": [{"name": n, "type": t} for n, t in correct],
            "missed": [{"name": n, "type": t} for n, t in missed],
            "extra": [{"name": n, "type": t} for n, t in extra],
            "variant_issues": variant_issues,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
    
    async def run_tests(self):
        """Запустить все тесты"""
        messages = self.load_test_messages()
        print(f"\n🚀 Запуск тестов: {len(messages)} сообщений\n")
        
        for message_data in messages:
            result = await self.process_message(message_data)
            
            # Сравнить результаты для v1 и v2
            comparison_v1 = self.compare_persons(
                result["expected_persons"],
                result["persons_v1"],
                "v1"
            )
            comparison_v2 = self.compare_persons(
                result["expected_persons"],
                result["persons_v2"],
                "v2"
            )
            
            result["comparison_v1"] = comparison_v1
            result["comparison_v2"] = comparison_v2
            self.results.append(result)
            
            print(f"   ✓ v1: {len(comparison_v1['correct'])}/{len(result['expected_persons'])} правильных")
            print(f"   ✓ v2: {len(comparison_v2['correct'])}/{len(result['expected_persons'])} правильных")
    
    def generate_report(self) -> str:
        """Сгенерировать Markdown отчет"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        report_path = Path(__file__).parent / "reports" / f"person_extraction_report_{timestamp}.md"
        
        report_lines = []
        report_lines.append("# Отчет по тестированию извлечения людей\n")
        report_lines.append(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_lines.append(f"**Тестовый пользователь ID:** {self.test_user.id}\n")
        report_lines.append(f"**Тестовая сессия ID:** {self.test_session.id}\n")
        report_lines.append(f"**Количество сообщений:** {len(self.results)}\n\n")
        
        # Общая статистика
        report_lines.append("## Общая статистика\n")
        
        total_expected = sum(len(r["expected_persons"]) for r in self.results)
        total_found_v1 = sum(len(r["comparison_v1"]["correct"]) for r in self.results)
        total_found_v2 = sum(len(r["comparison_v2"]["correct"]) for r in self.results)
        
        avg_precision_v1 = sum(r["comparison_v1"]["precision"] for r in self.results) / len(self.results) if self.results else 0
        avg_recall_v1 = sum(r["comparison_v1"]["recall"] for r in self.results) / len(self.results) if self.results else 0
        avg_f1_v1 = sum(r["comparison_v1"]["f1_score"] for r in self.results) / len(self.results) if self.results else 0
        
        avg_precision_v2 = sum(r["comparison_v2"]["precision"] for r in self.results) / len(self.results) if self.results else 0
        avg_recall_v2 = sum(r["comparison_v2"]["recall"] for r in self.results) / len(self.results) if self.results else 0
        avg_f1_v2 = sum(r["comparison_v2"]["f1_score"] for r in self.results) / len(self.results) if self.results else 0
        
        report_lines.append("| Метрика | Pipeline v1 | Pipeline v2 |\n")
        report_lines.append("|---------|-------------|-------------|\n")
        report_lines.append(f"| Найдено правильных | {total_found_v1}/{total_expected} | {total_found_v2}/{total_expected} |\n")
        report_lines.append(f"| Precision (среднее) | {avg_precision_v1:.2%} | {avg_precision_v2:.2%} |\n")
        report_lines.append(f"| Recall (среднее) | {avg_recall_v1:.2%} | {avg_recall_v2:.2%} |\n")
        report_lines.append(f"| F1 Score (среднее) | {avg_f1_v1:.2%} | {avg_f1_v2:.2%} |\n\n")
        
        # Детальный анализ по каждому сообщению
        report_lines.append("## Детальный анализ по сообщениям\n")
        
        for i, result in enumerate(self.results, 1):
            report_lines.append(f"### Сообщение {result['message_id']}\n")
            report_lines.append(f"**Текст:** {result['message_text']}\n")
            if result['notes']:
                report_lines.append(f"**Примечание:** {result['notes']}\n")
            report_lines.append("\n")
            
            # Pipeline v1
            report_lines.append("#### Pipeline v1\n")
            comp_v1 = result["comparison_v1"]
            report_lines.append(f"- **Найдено:** {comp_v1['actual_count']} | **Ожидалось:** {comp_v1['expected_count']} | **Правильных:** {len(comp_v1['correct'])}\n")
            report_lines.append(f"- **Precision:** {comp_v1['precision']:.2%} | **Recall:** {comp_v1['recall']:.2%} | **F1:** {comp_v1['f1_score']:.2%}\n\n")
            
            if comp_v1['correct']:
                report_lines.append("✅ **Правильно найденные:**\n")
                for p in comp_v1['correct']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            if comp_v1['missed']:
                report_lines.append("❌ **Пропущенные:**\n")
                for p in comp_v1['missed']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            if comp_v1['extra']:
                report_lines.append("⚠️ **Лишние:**\n")
                for p in comp_v1['extra']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            # Pipeline v2
            report_lines.append("#### Pipeline v2\n")
            comp_v2 = result["comparison_v2"]
            report_lines.append(f"- **Найдено:** {comp_v2['actual_count']} | **Ожидалось:** {comp_v2['expected_count']} | **Правильных:** {len(comp_v2['correct'])}\n")
            report_lines.append(f"- **Precision:** {comp_v2['precision']:.2%} | **Recall:** {comp_v2['recall']:.2%} | **F1:** {comp_v2['f1_score']:.2%}\n\n")
            
            if comp_v2['correct']:
                report_lines.append("✅ **Правильно найденные:**\n")
                for p in comp_v2['correct']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            if comp_v2['missed']:
                report_lines.append("❌ **Пропущенные:**\n")
                for p in comp_v2['missed']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            if comp_v2['extra']:
                report_lines.append("⚠️ **Лишние:**\n")
                for p in comp_v2['extra']:
                    report_lines.append(f"  - {p['name']} ({p['type']})\n")
                report_lines.append("\n")
            
            # Проблемы с вариантами имен
            if comp_v2['variant_issues']:
                report_lines.append("🔍 **Проблемы с вариантами имен:**\n")
                for issue in comp_v2['variant_issues']:
                    report_lines.append(f"  - Ожидалось: {issue['expected']}, найдено: {issue['found']} ({issue['issue']})\n")
                report_lines.append("\n")
        
        # Сравнение Pipeline v1 vs v2
        report_lines.append("## Сравнение Pipeline v1 vs v2\n\n")
        report_lines.append("| Метрика | v1 | v2 | Лучше |\n")
        report_lines.append("|---------|----|----|-------|\n")
        report_lines.append(f"| Precision | {avg_precision_v1:.2%} | {avg_precision_v2:.2%} | {'v2' if avg_precision_v2 > avg_precision_v1 else 'v1'} |\n")
        report_lines.append(f"| Recall | {avg_recall_v1:.2%} | {avg_recall_v2:.2%} | {'v2' if avg_recall_v2 > avg_recall_v1 else 'v1'} |\n")
        report_lines.append(f"| F1 Score | {avg_f1_v1:.2%} | {avg_f1_v2:.2%} | {'v2' if avg_f1_v2 > avg_f1_v1 else 'v1'} |\n\n")
        
        # Предложения по улучшению
        report_lines.append("## Предложения по улучшению\n\n")
        
        suggestions = []
        
        # Анализ пропущенных людей
        all_missed_v1 = []
        all_missed_v2 = []
        for r in self.results:
            all_missed_v1.extend(r["comparison_v1"]["missed"])
            all_missed_v2.extend(r["comparison_v2"]["missed"])
        
        if all_missed_v1:
            suggestions.append(f"- **Pipeline v1 пропустил {len(all_missed_v1)} человек:** {', '.join([p['name'] for p in all_missed_v1[:5]])}")
            suggestions.append("  - Рекомендация: Улучшить промпт extractor v3 для более агрессивного поиска всех людей")
        
        if all_missed_v2:
            suggestions.append(f"- **Pipeline v2 пропустил {len(all_missed_v2)} человек:** {', '.join([p['name'] for p in all_missed_v2[:5]])}")
            suggestions.append("  - Рекомендация: Улучшить промпт person_extractor v1 для поиска всех людей")
        
        # Анализ вариантов имен
        all_variants = []
        for r in self.results:
            all_variants.extend(r["comparison_v2"]["variant_issues"])
        
        if all_variants:
            suggestions.append(f"- **Обнаружено {len(all_variants)} проблем с вариантами имен**")
            suggestions.append("  - Рекомендация: Улучшить логику объединения вариантов имен в _apply_person_extractor_results_v2")
            suggestions.append("  - Рекомендация: Добавить более явные правила в промпт person_extractor про объединение вариантов")
        
        # Анализ лишних людей
        all_extra_v1 = []
        all_extra_v2 = []
        for r in self.results:
            all_extra_v1.extend(r["comparison_v1"]["extra"])
            all_extra_v2.extend(r["comparison_v2"]["extra"])
        
        if all_extra_v1:
            suggestions.append(f"- **Pipeline v1 нашел {len(all_extra_v1)} лишних человек:** {', '.join([p['name'] for p in all_extra_v1[:5]])}")
            suggestions.append("  - Рекомендация: Проверить, не извлекаются ли люди из message_history")
        
        if all_extra_v2:
            suggestions.append(f"- **Pipeline v2 нашел {len(all_extra_v2)} лишних человек:** {', '.join([p['name'] for p in all_extra_v2[:5]])}")
            suggestions.append("  - Рекомендация: Проверить логику person_extractor")
        
        if not suggestions:
            suggestions.append("- ✅ Все работает отлично! Нет критических проблем.")
        
        for suggestion in suggestions:
            report_lines.append(f"{suggestion}\n")
        
        report_lines.append("\n## Что работает хорошо\n\n")
        
        if avg_recall_v1 > 0.8 or avg_recall_v2 > 0.8:
            report_lines.append("- ✅ Высокий recall - большинство людей находится\n")
        if avg_precision_v1 > 0.8 or avg_precision_v2 > 0.8:
            report_lines.append("- ✅ Высокая precision - мало лишних людей\n")
        if avg_f1_v1 > 0.8 or avg_f1_v2 > 0.8:
            report_lines.append("- ✅ Хороший баланс между precision и recall\n")
        
        # Сохранить отчет
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(''.join(report_lines))
        
        return str(report_path)
    
    def cleanup(self):
        """Очистить тестовые данные"""
        if self.test_user:
            # Удалить связи MemoryPerson и MemoryChapter сначала
            from app.models import MemoryPerson, MemoryChapter, Memory
            if self.test_session:
                # Получить все memories для этой сессии
                memories = self.db.query(Memory).filter(Memory.session_id == self.test_session.id).all()
                memory_ids = [m.id for m in memories]
                
                if memory_ids:
                    # Сначала обнулить first_seen_memory_id у людей
                    self.db.query(Person).filter(
                        Person.first_seen_memory_id.in_(memory_ids)
                    ).update({Person.first_seen_memory_id: None}, synchronize_session=False)
                    # Удалить связи
                    self.db.query(MemoryPerson).filter(MemoryPerson.memory_id.in_(memory_ids)).delete()
                    self.db.query(MemoryChapter).filter(MemoryChapter.memory_id.in_(memory_ids)).delete()
                    # Удалить memories
                    self.db.query(Memory).filter(Memory.id.in_(memory_ids)).delete()
                
                # Удалить все сообщения
                self.db.query(Message).filter(Message.session_id == self.test_session.id).delete()
                # Удалить сессию
                self.db.delete(self.test_session)
            
            # Теперь можно удалить людей (связи уже удалены)
            self.db.query(Person).filter(Person.user_id == self.test_user.id).delete()
            # Удалить пользователя
            self.db.delete(self.test_user)
            self.db.commit()
            print(f"\n✓ Тестовые данные очищены")
    
    def close(self):
        """Закрыть соединение с БД"""
        self.db.close()


async def main():
    """Главная функция"""
    tester = PersonExtractionTester()
    try:
        tester.setup()
        await tester.run_tests()
        report_path = tester.generate_report()
        print(f"\n✅ Тесты завершены!")
        print(f"📄 Отчет сохранен: {report_path}")
    finally:
        tester.cleanup()
        tester.close()


if __name__ == "__main__":
    asyncio.run(main())
