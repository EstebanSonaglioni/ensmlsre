"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  getAccessToken,
  listNotifications,
  readAllNotifications,
  readNotification,
  type NotificationItem,
  type ProductQuestionItem,
  type SellItem,
  type SellMessageItem,
} from "./api";
import { wsUrl } from "./api-url";

type MessageHandler = (message: SellMessageItem) => void;
type StatusHandler = (sell: SellItem) => void;
type QuestionHandler = (question: ProductQuestionItem) => void;

type RealtimeContextValue = {
  notifications: NotificationItem[];
  unread: number;
  watchSell: (sellId: number) => void;
  unwatchSell: (sellId: number) => void;
  watchProduct: (productId: number) => void;
  unwatchProduct: (productId: number) => void;
  onSellMessage: (sellId: number, handler: MessageHandler) => () => void;
  onSellStatus: (sellId: number, handler: StatusHandler) => () => void;
  onProductQuestion: (productId: number, handler: QuestionHandler) => () => void;
  markRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
  unlockAudio: () => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

function playDing(ctx: AudioContext | null) {
  if (!ctx) {
    return;
  }
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = "sine";
  osc.frequency.value = 880;
  gain.gain.value = 0.08;
  osc.connect(gain);
  gain.connect(ctx.destination);
  osc.start();
  osc.stop(ctx.currentTime + 0.12);
}

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unread, setUnread] = useState(0);
  const socketRef = useRef<WebSocket | null>(null);
  const audioRef = useRef<AudioContext | null>(null);
  const watched = useRef(new Set<number>());
  const watchedProducts = useRef(new Set<number>());
  const messageHandlers = useRef(new Map<number, Set<MessageHandler>>());
  const statusHandlers = useRef(new Map<number, Set<StatusHandler>>());
  const questionHandlers = useRef(new Map<number, Set<QuestionHandler>>());

  const send = useCallback((payload: object) => {
    const socket = socketRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let retry: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      const token = getAccessToken();
      if (!token || cancelled) {
        return;
      }
      const socket = new WebSocket(wsUrl());
      socketRef.current = socket;
      socket.onopen = () => {
        socket.send(JSON.stringify({ type: "auth", token }));
        for (const sellId of watched.current) {
          socket.send(JSON.stringify({ type: "watch", sell_id: sellId }));
        }
        for (const productId of watchedProducts.current) {
          socket.send(
            JSON.stringify({ type: "watch", product_id: productId }),
          );
        }
      };
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as {
            type?: string;
            message?: SellMessageItem;
            sell?: SellItem;
            product_id?: number;
            question?: ProductQuestionItem;
            notification?: NotificationItem;
          };
          if (data.type === "message" && data.message) {
            const incoming = { ...data.message, mine: false };
            const handlers = messageHandlers.current.get(incoming.sell_id);
            handlers?.forEach((handler) => handler(incoming));
          }
          if (data.type === "status" && data.sell) {
            const handlers = statusHandlers.current.get(data.sell.id);
            handlers?.forEach((handler) => handler(data.sell!));
          }
          if (
            (data.type === "question" || data.type === "answer") &&
            data.question &&
            data.product_id
          ) {
            const handlers = questionHandlers.current.get(data.product_id);
            handlers?.forEach((handler) => handler(data.question!));
          }
          if (data.type === "notification" && data.notification) {
            setNotifications((current) => [
              data.notification!,
              ...current.filter((item) => item.id !== data.notification!.id),
            ]);
            setUnread((current) => current + 1);
            void playDing(audioRef.current);
          }
        } catch {
          /* ignore malformed frames */
        }
      };
      socket.onclose = () => {
        if (!cancelled) {
          retry = setTimeout(connect, 2000);
        }
      };
    }

    connect();
    listNotifications({ page_size: 20 })
      .then((result) => {
        if (!cancelled) {
          setNotifications(result.items);
          setUnread(result.unread);
        }
      })
      .catch(() => {
        /* campana vacía */
      });

    return () => {
      cancelled = true;
      if (retry) {
        clearTimeout(retry);
      }
      socketRef.current?.close();
    };
  }, []);

  const watchSell = useCallback(
    (sellId: number) => {
      watched.current.add(sellId);
      send({ type: "watch", sell_id: sellId });
    },
    [send],
  );

  const unwatchSell = useCallback(
    (sellId: number) => {
      watched.current.delete(sellId);
      send({ type: "unwatch", sell_id: sellId });
    },
    [send],
  );

  const watchProduct = useCallback(
    (productId: number) => {
      watchedProducts.current.add(productId);
      send({ type: "watch", product_id: productId });
    },
    [send],
  );

  const unwatchProduct = useCallback(
    (productId: number) => {
      watchedProducts.current.delete(productId);
      send({ type: "unwatch", product_id: productId });
    },
    [send],
  );

  const onSellMessage = useCallback(
    (sellId: number, handler: MessageHandler) => {
      const set = messageHandlers.current.get(sellId) ?? new Set();
      set.add(handler);
      messageHandlers.current.set(sellId, set);
      return () => {
        set.delete(handler);
      };
    },
    [],
  );

  const onSellStatus = useCallback(
    (sellId: number, handler: StatusHandler) => {
      const set = statusHandlers.current.get(sellId) ?? new Set();
      set.add(handler);
      statusHandlers.current.set(sellId, set);
      return () => {
        set.delete(handler);
      };
    },
    [],
  );

  const onProductQuestion = useCallback(
    (productId: number, handler: QuestionHandler) => {
      const set = questionHandlers.current.get(productId) ?? new Set();
      set.add(handler);
      questionHandlers.current.set(productId, set);
      return () => {
        set.delete(handler);
      };
    },
    [],
  );

  const markRead = useCallback(async (id: number) => {
    const updated = await readNotification(id);
    setNotifications((current) =>
      current.map((item) => (item.id === id ? updated : item)),
    );
    setUnread((current) => Math.max(0, current - 1));
  }, []);

  const markAllRead = useCallback(async () => {
    await readAllNotifications();
    setNotifications((current) =>
      current.map((item) =>
        item.read_at ? item : { ...item, read_at: new Date().toISOString() },
      ),
    );
    setUnread(0);
  }, []);

  const unlockAudio = useCallback(() => {
    if (!audioRef.current) {
      const Ctor =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext;
      if (Ctor) {
        audioRef.current = new Ctor();
      }
    }
    void audioRef.current?.resume();
  }, []);

  const value = useMemo(
    () => ({
      notifications,
      unread,
      watchSell,
      unwatchSell,
      watchProduct,
      unwatchProduct,
      onSellMessage,
      onSellStatus,
      onProductQuestion,
      markRead,
      markAllRead,
      unlockAudio,
    }),
    [
      notifications,
      unread,
      watchSell,
      unwatchSell,
      watchProduct,
      unwatchProduct,
      onSellMessage,
      onSellStatus,
      onProductQuestion,
      markRead,
      markAllRead,
      unlockAudio,
    ],
  );

  return (
    <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const value = useContext(RealtimeContext);
  if (!value) {
    throw new Error("realtime");
  }
  return value;
}
