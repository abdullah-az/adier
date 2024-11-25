export interface مادة {
  id: number;
  اسم: string;
  الاسئلة?: سؤال[];
  تاريخ_الانشاء: Date;
  تاريخ_التحديث: Date;
}

export interface سؤال {
  id: number;
  نص_السؤال: string;
  الشرح?: string | null;
  المادة_id: number;
  المادة?: مادة;
  الخيارات?: خيار[];
  تاريخ_الانشاء: Date;
  تاريخ_التحديث: Date;
}

export interface خيار {
  id: number;
  النص: string;
  صحيح: boolean;
  السؤال_id: number;
  السؤال?: سؤال;
  تاريخ_الانشاء: Date;
  تاريخ_التحديث: Date;
}