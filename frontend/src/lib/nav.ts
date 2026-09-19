import { writable } from 'svelte/store';

export type PageId = 'dashboard' | 'workshops' | 'mills' | 'samples' | 'passes';

export const page = writable<PageId>('dashboard');

/** 跳转到研磨机列表时携带的车间筛选（消费后清空） */
export const millWorkshopFilter = writable<number | null>(null);
