import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const المواد = {
  اضافة: async (اسم: string) => {
    return await prisma.المواد.create({
      data: { اسم }
    });
  },

  الكل: async () => {
    return await prisma.المواد.findMany({
      include: {
        الاسئلة: true
      }
    });
  },

  حذف: async (id: number) => {
    return await prisma.المواد.delete({
      where: { id }
    });
  },

  تعديل: async (id: number, اسم: string) => {
    return await prisma.المواد.update({
      where: { id },
      data: { اسم }
    });
  }
};

export const الاسئلة = {
  اضافة: async (بيانات: {
    نص_السؤال: string,
    الشرح?: string,
    المادة_id: number,
    الخيارات: { النص: string, صحيح: boolean }[]
  }) => {
    return await prisma.الاسئلة.create({
      data: {
        نص_السؤال: بيانات.نص_السؤال,
        الشرح: بيانات.الشرح,
        المادة_id: بيانات.المادة_id,
        الخيارات: {
          create: بيانات.الخيارات
        }
      },
      include: {
        الخيارات: true
      }
    });
  },

  حسب_المادة: async (مادة_id: number) => {
    return await prisma.الاسئلة.findMany({
      where: { المادة_id },
      include: {
        الخيارات: true
      }
    });
  },

  حذف: async (id: number) => {
    return await prisma.الاسئلة.delete({
      where: { id }
    });
  },

  تعديل: async (id: number, بيانات: {
    نص_السؤال?: string,
    الشرح?: string,
    الخيارات?: { id: number, النص: string, صحيح: boolean }[]
  }) => {
    const { الخيارات, ...باقي_البيانات } = بيانات;

    const سؤال = await prisma.الاسئلة.update({
      where: { id },
      data: باقي_البيانات
    });

    if (الخيارات) {
      for (const خيار of الخيارات) {
        await prisma.الخيارات.update({
          where: { id: خيار.id },
          data: {
            النص: خيار.النص,
            صحيح: خيار.صحيح
          }
        });
      }
    }

    return await prisma.الاسئلة.findUnique({
      where: { id },
      include: {
        الخيارات: true
      }
    });
  }
};