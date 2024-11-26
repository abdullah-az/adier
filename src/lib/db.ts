import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const subjects = {
  create: async (name: string, specialization: string) => {
    return await prisma.subject.create({
       { name, specialization }
    });
  },

  findAll: async () => {
    return await prisma.subject.findMany({
      include: { questions: true }
    });
  },

  delete: async (id: number) => {
    return await prisma.subject.delete({
      where: { id }
    });
  },

  update: async (id: number, name: string, specialization: string) => {
    return await prisma.subject.update({
      where: { id },
       { name, specialization }
    });
  }
};

export const questions = {
  create: async ( {
    text: string;
    explanation: string | null;
    subjectId: number;
    options: { text: string; isCorrect: boolean }[];
  }) => {
    return prisma.$transaction(async (tx) => {
      const question = await tx.question.create({
         {
          text: data.text,
          explanation: data.explanation,
          subject: { connect: { id: data.subjectId } },
        },
      });

      await tx.option.createMany({
         data.options.map((option) => ({
          text: option.text,
          isCorrect: option.isCorrect,
          questionId: question.id,
        })),
      });

      return await tx.question.findUnique({
        where: { id: question.id },
        include: { options: true },
      });
    });
  },

  findBySubjectId: async (subjectId: number) => {
    return await prisma.question.findMany({
      where: { subjectId },
      include: { options: true }
    });
  },

  delete: async (id: number) => {
    return await prisma.question.delete({
      where: { id }
    });
  },

  update: async (id: number,  {
    text?: string;
    explanation?: string | null;
    options?: { id: number; text: string; isCorrect: boolean }[];
  }) => {
    const { options, ...rest } = data;

    const question = await prisma.question.update({
      where: { id },
       rest,
    });

    if (options) {
      await prisma.$transaction(async (tx) => {
        await tx.option.updateMany({
          where: { questionId: id },
           {
            text: (params: { id: number }) => options?.find((o) => o.id === params.id)?.text,
            isCorrect: (params: { id: number }) => options?.find((o) => o.id === params.id)?.isCorrect,
          },
        });
      });
    }

    return await prisma.question.findUnique({
      where: { id },
      include: { options: true },
    });
  },
};
