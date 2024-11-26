export interface Subject {
  id: number;
  name: string;
  questions?: Question[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Question {
  id: number;
  text: string;
  explanation?: string | null;
  subjectId: number;
  subject?: Subject;
  options?: Option[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Option {
  id: number;
  text: string;
  isCorrect: boolean;
  questionId: number;
  question?: Question;
  createdAt: Date;
  updatedAt: Date;
}
