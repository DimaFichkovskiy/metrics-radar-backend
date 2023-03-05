from typing import List
from sqlalchemy import select
from fastapi import HTTPException, Depends

from src.crud import CompanyCRUD
from src.database import AsyncSession, get_db_session
from src.models.worker import Role
from src import schemas, models


class QuizCrud:

    def __init__(
            self,
            db: AsyncSession = Depends(get_db_session),
            company_crud: CompanyCRUD = Depends(),
    ):
        self.db: AsyncSession = db
        self.company_crud = company_crud

    async def get_all_quizzes(self, company_id: int, skip: int = 0, limit: int = 100) -> List[models.Quiz]:
        result = await self.db.execute(select(models.Quiz).filter(
            models.Quiz.company_id == company_id
        ).offset(skip).limit(limit))
        return result.scalars().all()

    async def check_main_role_by_user_id_and_company_id(
            self, user_id: int, company_id: int
    ):
        result = await self.db.execute(select(models.User).join(models.Worker).filter(
            ((models.Worker.user_id == user_id) & (models.Worker.company_id == company_id)) &
            ((models.Worker.role == Role.owner) | (models.Worker.role == Role.admin))
        ))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=400, detail="The user is not the owner or administrator of this company")
        return result

    async def get_quiz_by_id(self, quiz_id: int) -> models.Quiz:
        result = await self.db.execute(select(models.Quiz).filter(models.Quiz.id == quiz_id))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Not Found Quiz")
        return result

    async def get_questions_by_quiz_id(self, quiz_id: int) -> List[models.Question]:
        result = await self.db.execute(select(models.Question).filter(models.Question.quiz_id == quiz_id))
        return result.scalars().all()

    async def get_question_by_id_and_quiz_id(self, question_id: int, quiz_id: int) -> models.Question:
        result = await self.db.execute(select(models.Question).filter(
            (models.Question.id == question_id) & (models.Question.quiz_id == quiz_id)
        ))
        result = result.scalars().first()
        if not result:
            raise HTTPException(status_code=404, detail="Not Found Question")
        return result

    async def get_answers_by_quiz_id(self, quiz_id: int) -> List[models.Answer]:
        result = await self.db.execute(select(models.Answer).join(models.Question).join(models.Quiz).filter(
            models.Quiz.id == quiz_id
        ))
        return result.scalars().all()

    async def get_correct_answers_by_quiz_id(self, quiz_id: int) -> List[models.Answer]:
        result = await self.db.execute(select(models.Answer).join(models.Question).join(models.Quiz).filter(
            (models.Quiz.id == quiz_id) & (models.Answer.is_correct == True)
        ))
        return result.scalars().all()

    async def get_answers_by_question_id(self, question_id: int) -> List[models.Answer]:
        result = await self.db.execute(select(models.Answer).filter(models.Answer.question_id == question_id))
        return result.scalars().all()

    async def create_quiz(
            self, quiz_data: schemas.CreateQuiz, company_id: int, user_id: int
    ) -> schemas.QuizResponse:
        company = await self.company_crud.get_company_by_id(company_id=company_id)

        await self.check_main_role_by_user_id_and_company_id(user_id=user_id, company_id=company_id)

        quiz = models.Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            passing_frequency=quiz_data.passing_frequency,
            number_of_questions=len(quiz_data.list_questions),
            company=company
        )

        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)

        questions = await self.create_questions_to_quiz(questions_data=quiz_data.list_questions, quiz=quiz)

        await self.db.refresh(quiz)
        return schemas.QuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            passing_frequency=quiz.passing_frequency,
            number_of_questions=quiz.number_of_questions,
            list_questions=questions
        )

    async def create_questions_to_quiz(
            self, questions_data: List[schemas.Question], quiz: models.Quiz
    ) -> List[schemas.QuestionsResponse]:
        questions_list = list()
        for question_data in questions_data:
            question = models.Question(
                question=question_data.question,
                quiz=quiz
            )

            self.db.add(question)
            await self.db.commit()
            await self.db.refresh(question)
            question_id = question.id
            question_title = question.question

            answers = await self.create_answers_to_question(
                answers_data=question_data.answer_options,
                correct_answer=question_data.correct_answer,
                question=question
            )

            questions_list.append(
                schemas.QuestionsResponse(
                    id=question_id, question=question_title, answer_options=answers
                )
            )
        return questions_list

    async def create_answers_to_question(
            self, answers_data: list, correct_answer: int, question: models.Question
    ) -> List[schemas.AnswerResponse]:
        answers_list = list()
        counter = 0

        for answer_data in answers_data:
            if correct_answer == counter:
                answer = models.Answer(
                    answer=answer_data,
                    is_correct=True,
                    question=question
                )
            else:
                answer = models.Answer(
                    answer=answer_data,
                    is_correct=False,
                    question=question
                )

            self.db.add(answer)
            await self.db.commit()
            await self.db.refresh(answer)

            answers_list.append(
                schemas.AnswerResponse(
                    id=answer.id, answer=answer.answer, is_correct=answer.is_correct
                )
            )

            counter += 1

        return answers_list

    async def add_questions_to_quiz(
            self, questions_data: List[schemas.Question], company_id: int, quiz_id: int, user_id: int
    ) -> schemas.QuizResponse:
        await self.check_main_role_by_user_id_and_company_id(user_id=user_id, company_id=company_id)

        quiz = await self.get_quiz_by_id(quiz_id=quiz_id)

        questions = await self.create_questions_to_quiz(questions_data=questions_data, quiz=quiz)

        await self.db.refresh(quiz)
        quiz.number_of_questions += len(questions)

        await self.db.commit()
        await self.db.refresh(quiz)

        return schemas.QuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            passing_frequency=quiz.passing_frequency,
            number_of_questions=quiz.number_of_questions,
            list_questions=questions
        )

    async def remove_question_from_quiz(
            self, company_id: int, user_id: int, quiz_id: int, question_id: int
    ) -> schemas.QuizResponse:
        await self.check_main_role_by_user_id_and_company_id(user_id=user_id, company_id=company_id)

        quiz = await self.get_quiz_by_id(quiz_id=quiz_id)

        await self.delete_answers_by_question_id(question_id=question_id)
        await self.delete_question_by_id_and_quiz_id(question_id=question_id, quiz_id=quiz_id)

        await self.db.refresh(quiz)
        quiz.number_of_questions -= 1

        await self.db.commit()
        await self.db.refresh(quiz)

        questions_list = list()
        questions = await self.get_questions_by_quiz_id(quiz_id=quiz_id)
        for question in questions:
            answers = await self.get_answers_by_question_id(question.id)
            questions_list.append(
                schemas.QuestionsResponse(
                    id=question.id, question=question.question, answer_options=answers
                )
            )

        return schemas.QuizResponse(
            id=quiz.id,
            title=quiz.title,
            description=quiz.description,
            passing_frequency=quiz.passing_frequency,
            list_questions=questions_list,
            number_of_questions=quiz.number_of_questions
        )

    async def delete_quiz(self, user_id: int, company_id: int, quiz_id: int):
        await self.check_main_role_by_user_id_and_company_id(user_id=user_id, company_id=company_id)

        await self.delete_answers_by_quiz_id(quiz_id=quiz_id)
        await self.delete_questions_by_quiz_id(quiz_id=quiz_id)

        quiz = await self.get_quiz_by_id(quiz_id=quiz_id)
        await self.db.delete(quiz)
        await self.db.commit()

    async def delete_question_by_id_and_quiz_id(self, question_id: int, quiz_id: int):
        question = await self.get_question_by_id_and_quiz_id(question_id=question_id, quiz_id=quiz_id)

        await self.db.delete(question)
        await self.db.commit()

    async def delete_questions_by_quiz_id(self, quiz_id: int):
        questions = await self.get_questions_by_quiz_id(quiz_id=quiz_id)

        for question in questions:
            await self.db.delete(question)
        await self.db.commit()

    async def delete_answers_by_question_id(self, question_id: int):
        answers = await self.get_answers_by_question_id(question_id=question_id)
        for answer in answers:
            await self.db.delete(answer)
        await self.db.commit()

    async def delete_answers_by_quiz_id(self, quiz_id: int):
        answers = await self.get_answers_by_quiz_id(quiz_id=quiz_id)

        for answer in answers:
            await self.db.delete(answer)
        await self.db.commit()
