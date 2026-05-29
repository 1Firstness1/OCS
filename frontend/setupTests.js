import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Настройка глобальных моков, например, window.alert или fetch
global.alert = vi.fn();
global.confirm = vi.fn(() => true);
