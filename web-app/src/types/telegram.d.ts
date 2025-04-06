// src/telegram.d.ts

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
  is_bot?: boolean;
}

interface TelegramInitDataUnsafe {
  user?: TelegramUser;
  auth_date?: number;
  hash?: string;
}

interface TelegramWebApp {
  initData?: string;
  initDataUnsafe: TelegramInitDataUnsafe;
  expand: () => void;
  close: () => void;
  sendData: (data: string) => void;
  onEvent: (eventType: string, callback: () => void) => void;
  offEvent: (eventType: string, callback: () => void) => void;
  isExpanded: boolean;
  version: string;
  platform: string;
  colorScheme: "light" | "dark";
  headerColor?: string;
  backgroundColor?: string;
  isClosingConfirmationEnabled?: boolean;
}

interface Window {
  Telegram?: {
    WebApp: TelegramWebApp;
  };
}
