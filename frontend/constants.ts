import type { Message, Request } from './types';
import { RequestStatus } from './types';

export const MOCK_MESSAGES: Message[] = [];

export const MOCK_REQUESTS: Request[] = [
  {
    id: 'req1',
    messageId: 'msg1',
    requestType: 'Abandoned Vehicle',
    status: RequestStatus.SUBMITTED,
    submittedAt: '2024-07-29T10:30:31Z',
    sf311CaseId: '24-00123456',
  },
  {
    id: 'req2',
    messageId: 'msg2',
    requestType: 'Pothole or Street Defect',
    status: RequestStatus.SUBMITTED,
    submittedAt: '2024-07-29T11:05:59Z',
    sf311CaseId: '24-00123478',
  },
  {
    id: 'req3',
    messageId: 'msg3',
    requestType: 'Graffiti',
    status: RequestStatus.SUBMITTED,
    submittedAt: '2024-07-29T12:15:24Z',
    sf311CaseId: '24-00123512',
  },
  {
    id: 'req4',
    messageId: 'msg4',
    requestType: 'Streetlight Repair',
    status: RequestStatus.PENDING,
    submittedAt: '2024-07-29T12:45:35Z',
    sf311CaseId: undefined,
  },
];