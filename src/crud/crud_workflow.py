import csv
import json

import aioredis

from datetime import datetime, timedelta
from typing import List
from sqlalchemy import select
from fastapi import Depends

from src.crud import QuizCrud, UserCRUD, CompanyCRUD
from src.database import AsyncSession, get_db_session
from src import schemas, models
from src.config import Config


class WorkflowCrud:

    def __init__(
            self,
            db: AsyncSession = Depends(get_db_session),
            quiz_crud: QuizCrud = Depends(),
            company_crud: CompanyCRUD = Depends(),
            user_crud: UserCRUD = Depends()
    ):
        self.db: AsyncSession = db
        self.quiz_crud = quiz_crud
        self.company_crud = company_crud
        self.user_crud = user_crud

    async def get_number_of_correct_answers(
            self, answers_from_user: List[schemas.AnswersFromUser], quiz_id: int
    ) -> int:
        correct_answers = await self.quiz_crud.get_correct_answers_by_quiz_id(quiz_id=quiz_id)

        number_of_correct_answers = 0
        for answer_from_user in answers_from_user:
            for correct_answer in correct_answers:
                if answer_from_user.question_id == correct_answer.question_id:
                    if answer_from_user.answer_id == correct_answer.id:
                        number_of_correct_answers += 1
                        correct_answers.remove(correct_answer)
                        break

        return number_of_correct_answers

    async def get_general_result_by_user_and_company_id(self, user_id: int, company_id: int) -> models.GeneralResult:
        result = await self.db.execute(select(models.GeneralResult).filter(
            (models.GeneralResult.user_id == user_id) & (models.GeneralResult.company_id == company_id)
        ))
        return result.scalars().first()

    async def create_quiz_result(
            self,
            answers_from_user: List[schemas.AnswersFromUser],
            user_id: int,
            quiz: models.Quiz,
            general_result: models.GeneralResult
    ):
        redis = await aioredis.from_url(Config.REDIS_URL)
        number_of_correct_answers = await self.get_number_of_correct_answers(
            answers_from_user=answers_from_user, quiz_id=quiz.id
        )
        quiz_result = models.QuizResult(
            correct_answers=number_of_correct_answers,
            quiz=quiz,
            general_result=general_result,
            gpa=number_of_correct_answers/quiz.number_of_questions
        )
        self.db.add(quiz_result)
        await self.db.commit()
        await self.db.refresh(quiz_result)
        for answer_from_user in answers_from_user:
            await redis.set(f"{user_id}_{answer_from_user.question_id}", f"{answer_from_user.answer_id}")
        return quiz_result

    async def create_general_result_for_user(
            self, answers_from_user: List[schemas.AnswersFromUser], quiz_id: int, company_id: int, user_id: int
    ) -> schemas.TestResponse:
        user = await self.user_crud.get_user(user_id=user_id)
        company = await self.company_crud.get_company_by_id(company_id=company_id)
        quiz = await self.quiz_crud.get_quiz_by_id(quiz_id=quiz_id)
        general_result = models.GeneralResult(
            user=user,
            company=company,
        )
        self.db.add(general_result)
        await self.db.commit()
        await self.db.refresh(general_result)

        quiz_result = await self.create_quiz_result(
            answers_from_user=answers_from_user, user_id=user_id, quiz=quiz, general_result=general_result
        )

        gpa = quiz_result.correct_answers / quiz.number_of_questions
        general_result.gpa = gpa
        await self.db.commit()
        await self.db.refresh(quiz)

        return schemas.TestResponse(
            quiz_id=quiz_id,
            number_of_questions=quiz.number_of_questions,
            correct_answers=quiz_result.correct_answers,
            gpa=gpa
        )

    async def get_gpa(self, quizzes_results: List[models.QuizResult]) -> float:
        sum_of_correct_answers = 0
        sum_of_questions = 0
        for quiz_result in quizzes_results:
            sum_of_correct_answers += quiz_result.correct_answers
            quiz = await self.quiz_crud.get_quiz_by_id(quiz_id=quiz_result.quiz_id)
            sum_of_questions += quiz.number_of_questions

        gpa = sum_of_correct_answers/sum_of_questions
        return gpa

    async def get_all_gpa_by_user_id_and_time(self, user_id: int, time: datetime) -> List[models.GeneralResult]:
        result = await self.db.execute(select(models.GeneralResult).filter(
            (models.GeneralResult.user_id == user_id) & (models.GeneralResult.update_date >= time)
        ))
        return result.scalars().all()

    async def update_general_result_for_user(
            self, answers_from_user: List[schemas.AnswersFromUser], quiz_id: int, company_id: int, user_id: int
    ):
        quiz = await self.quiz_crud.get_quiz_by_id(quiz_id=quiz_id)
        general_result = await self.get_general_result_by_user_and_company_id(user_id=user_id, company_id=company_id)

        quiz_result = await self.create_quiz_result(
            answers_from_user=answers_from_user, user_id=user_id, quiz=quiz, general_result=general_result
        )

        gpa = await self.get_gpa(quizzes_results=general_result.quizzes_results)

        general_result.gpa = gpa
        await self.db.commit()
        await self.db.refresh(quiz)

        return schemas.TestResponse(
            quiz_id=quiz_id,
            number_of_questions=quiz.number_of_questions,
            correct_answers=quiz_result.correct_answers,
            gpa=general_result.gpa
        )

    async def get_all_gpa_by_time_and_company_id(self, time: datetime, company_id: int) -> List[models.GeneralResult]:
        result = await self.db.execute(select(models.GeneralResult).filter(
            (models.GeneralResult.company_id == company_id) &
            (models.GeneralResult.update_date >= time)
        ))
        return result.scalars().all()

    async def get_gpa_for_all_user(
            self, company_id: int, time_in_hours: int, user_id: int
    ) -> List[schemas.UserGPAResponse]:
        await self.company_crud.get_company_where_im_owner_or_admin_by_company_id(
            company_id=company_id, user_id=user_id
        )
        now_datetime = datetime.utcnow() - timedelta(hours=time_in_hours)

        list_gpa_all_users = await self.get_all_gpa_by_time_and_company_id(time=now_datetime, company_id=company_id)
        result = list()
        for user_gpa in list_gpa_all_users:
            result.append(
                schemas.UserGPAResponse(
                    user_id=user_gpa.id,
                    gpa=user_gpa.gpa
                )
            )

        return result

    async def get_user_quizzes(self, user_id: int, company_id: int, time: datetime) -> List[models.QuizResult]:
        result = await self.db.execute(select(models.QuizResult).join(models.GeneralResult).filter(
            (models.GeneralResult.user_id == user_id) &
            (models.GeneralResult.company_id == company_id) &
            (models.GeneralResult.update_date >= time)

        ))
        return result.scalars().all()

    async def get_gpa_all_user_quizzes(
            self, company_id: int, worker_id: int, time_in_hours: int, user_id: int
    ) -> List[schemas.UserGPAQuizResponse]:
        await self.company_crud.get_company_where_im_owner_or_admin_by_company_id(
            company_id=company_id, user_id=user_id
        )
        datetime_for_filter = datetime.utcnow() - timedelta(hours=time_in_hours)

        list_user_gpa_quizzes = await self.get_user_quizzes(
            user_id=worker_id, company_id=company_id, time=datetime_for_filter
        )
        result = list()
        for user_quiz_gpa in list_user_gpa_quizzes:
            result.append(
                schemas.UserGPAQuizResponse(
                    user_id=worker_id,
                    quiz_id=user_quiz_gpa.id,
                    gpa=user_quiz_gpa.gpa
                )
            )
        return result

    async def get_quizzes_result_by_user_id(self, user_id: int) -> models.GeneralResult:
        result = await self.db.execute(select(models.GeneralResult).filter(models.GeneralResult.user_id == user_id))
        return result.scalars().first()

    async def get_users_with_time_of_last_test(
            self, company_id: int, user_id: int
    ) -> List[schemas.UserWithTimeOfLastTestResponse]:
        await self.company_crud.get_company_where_im_owner_or_admin_by_company_id(
            company_id=company_id, user_id=user_id
        )

        workers = await self.company_crud.get_workers_by_company_id(company_id=company_id)
        result = list()
        for worker in workers:
            quizzes_result = await self.get_quizzes_result_by_user_id(user_id=worker.user_id)
            if not quizzes_result:
                result.append(
                    schemas.UserWithTimeOfLastTestResponse(
                        user_id=worker.user_id,
                        time=None
                    )
                )
            else:
                result.append(
                    schemas.UserWithTimeOfLastTestResponse(
                        user_id=worker.user_id,
                        time=quizzes_result.update_date
                    )
                )
        return result

    async def get_my_gpa(self, user_id: int, time_in_hours: int) -> List[schemas.MyGPA]:
        datetime_for_filter = datetime.utcnow() - timedelta(hours=time_in_hours)
        list_gpa = await self.get_all_gpa_by_user_id_and_time(user_id=user_id, time=datetime_for_filter)
        result = list()
        for gpa in list_gpa:
            result.append(
                schemas.MyGPA(
                    company_id=gpa.company_id,
                    gpa=gpa.gpa
                )
            )
        return result

    async def get_all_quizzes_result_by_user_id(self, user_id: int) -> List[models.QuizResult]:
        result = await self.db.execute(select(models.QuizResult).join(models.GeneralResult).filter(
            models.GeneralResult.user_id == user_id
        ))
        return result.scalars().all()

    async def get_my_quizzes_with_time_of_last_test(self, user_id: int) -> List[schemas.QuizWithTimeOfLastTestResponse]:
        quizzes_result = await self.get_all_quizzes_result_by_user_id(user_id=user_id)
        result = list()
        for quiz in quizzes_result:
            result.append(
                schemas.QuizWithTimeOfLastTestResponse(
                    quiz_id=quiz.id,
                    time=quiz.date_of_passage
                )
            )
        return result

    async def export_my_quizzes_results(self, user_id: int):
        redis = await aioredis.from_url(Config.REDIS_URL)
        keys = await redis.keys(f"*{user_id}*")

        file = open("my_quizzes_results", "w", newline='')
        # writer = csv.writer(file, delomiter=' ')
        print(keys)
        for key in keys:
            answer = json.loads(await redis.get(key))
