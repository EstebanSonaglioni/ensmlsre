import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true,
});

let accessToken: string | null = null;
let csrfToken: string | null = null;

export type RegisterResult = {
  email: string;
  role: string;
  access_token: string;
  csrf_token: string;
  balance: string;
  display_name: string;
  has_avatar: boolean;
};

function rememberAccessToken(token: string) {
  accessToken = token;
  api.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
}

function rememberSession(data: RegisterResult) {
  rememberAccessToken(data.access_token);
  csrfToken = data.csrf_token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export async function register(
  email: string,
  password: string,
): Promise<RegisterResult> {
  const { data } = await api.post<RegisterResult>("/auth/register", {
    email,
    password,
  });
  rememberSession(data);
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<RegisterResult> {
  const { data } = await api.post<RegisterResult>("/auth/login", {
    email,
    password,
  });
  rememberSession(data);
  return data;
}

export async function restoreSession(): Promise<RegisterResult | null> {
  try {
    const { data } = await api.get<RegisterResult>("/auth/me");
    rememberSession(data);
    return data;
  } catch {
    return null;
  }
}

function forgetAccessToken() {
  accessToken = null;
  csrfToken = null;
  delete api.defaults.headers.common.Authorization;
}

export type ProfileResult = {
  email: string;
  role: string;
  display_name: string;
  has_avatar: boolean;
  balance: string;
};

export async function updateProfile(fields: {
  display_name: string;
  image?: File | null;
}): Promise<ProfileResult> {
  const body = new FormData();
  body.append("display_name", fields.display_name);
  if (fields.image) {
    body.append("image", fields.image);
  }
  const { data } = await api.patch<ProfileResult>("/auth/profile", body);
  return data;
}

export async function fetchProfileImage(): Promise<string> {
  const { data, status } = await api.get<Blob>("/auth/profile/image", {
    responseType: "blob",
  });
  if (status !== 200 || !data.type.startsWith("image/")) {
    throw new Error("image");
  }
  return URL.createObjectURL(data);
}

export async function logout(): Promise<void> {
  try {
    await api.post(
      "/auth/logout",
      {},
      { headers: { "X-CSRF-Token": csrfToken || "" } },
    );
  } finally {
    forgetAccessToken();
  }
}

export type CreateStoreResult = {
  name: string;
  role: string;
};

export async function createStore(name: string): Promise<CreateStoreResult> {
  const { data } = await api.post<CreateStoreResult>("/stores", { name });
  return data;
}

export type StoreItem = {
  id: number;
  name: string;
  role: string;
};

export type StoreListResult = {
  items: StoreItem[];
  total: number;
  page: number;
  page_size: number;
};

export type InvitationItem = {
  email: string;
  store: string;
};

export type InvitationListResult = {
  items: InvitationItem[];
  total: number;
  page: number;
  page_size: number;
};

export async function createInvitation(
  email: string,
  store: string,
): Promise<InvitationItem> {
  const { data } = await api.post<InvitationItem>("/stores/invitations", {
    email,
    store,
  });
  return data;
}

export async function listInvitations(params: {
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<InvitationListResult> {
  const { data } = await api.get<InvitationListResult>("/stores/invitations", {
    params,
  });
  return data;
}

export async function acceptInvitation(store: string): Promise<{
  store: string;
  role: string;
}> {
  const { data } = await api.post<{ store: string; role: string }>(
    "/stores/invitations/accept",
    { store },
  );
  return data;
}

export type ProductItem = {
  id: number;
  store_id: number;
  store_name: string;
  name: string;
  quantity: number;
  price: string;
  net_profit?: string | null;
  category: string;
  subcategory: string;
  paused: boolean;
  ships: boolean;
  pickup: boolean;
};

export type ProductQuestionItem = {
  id: number;
  asker_label: string;
  asker_email?: string | null;
  text: string;
  answer: string | null;
};

export type SellerQuestionStatus = "pending" | "answered" | "all";
export type SellerQuestionSort =
  | "score"
  | "wait"
  | "net_profit"
  | "created_at"
  | "name";

export type SellerQuestionItem = {
  id: number;
  product_id: number;
  product_name: string;
  text: string;
  answer: string | null;
  created_at: string;
  wait_hours: string;
  net_profit: string;
  score: string;
};

export type SellerQuestionListResult = {
  items: SellerQuestionItem[];
  total: number;
  page: number;
  page_size: number;
};

export type ProductDetail = ProductItem & {
  questions: ProductQuestionItem[];
  can_manage: boolean;
};

export type ProductListResult = {
  items: ProductItem[];
  total: number;
  page: number;
  page_size: number;
};

export async function createProduct(
  storeId: number,
  fields: {
    name: string;
    quantity: string;
    price: string;
    net_profit: string;
    category: string;
    subcategory: string;
    ships: boolean;
    pickup: boolean;
    image: File;
  },
): Promise<ProductItem> {
  const body = new FormData();
  body.append("name", fields.name);
  body.append("quantity", fields.quantity);
  body.append("price", fields.price);
  body.append("net_profit", fields.net_profit || "0");
  body.append("category", fields.category);
  body.append("subcategory", fields.subcategory);
  body.append("ships", String(fields.ships));
  body.append("pickup", String(fields.pickup));
  body.append("image", fields.image);
  const { data } = await api.post<ProductItem>(
    `/stores/${storeId}/products`,
    body,
  );
  return data;
}

export async function listProducts(params: {
  page?: number;
  page_size?: number;
  q?: string;
}): Promise<ProductListResult> {
  const { data } = await api.get<ProductListResult>("/products", { params });
  return data;
}

export async function listMyProducts(params: {
  page?: number;
  page_size?: number;
}): Promise<ProductListResult> {
  const { data } = await api.get<ProductListResult>("/products/mine", {
    params,
  });
  return data;
}

export async function getProduct(id: number): Promise<ProductDetail> {
  const { data } = await api.get<ProductDetail>(`/products/${id}`);
  return data;
}

export async function updateProduct(
  id: number,
  fields: {
    name: string;
    quantity: string;
    price: string;
    net_profit: string;
    category: string;
    subcategory: string;
    ships: boolean;
    pickup: boolean;
    image?: File | null;
  },
): Promise<ProductItem> {
  const body = new FormData();
  body.append("name", fields.name);
  body.append("quantity", fields.quantity);
  body.append("price", fields.price);
  body.append("net_profit", fields.net_profit || "0");
  body.append("category", fields.category);
  body.append("subcategory", fields.subcategory);
  body.append("ships", String(fields.ships));
  body.append("pickup", String(fields.pickup));
  if (fields.image) {
    body.append("image", fields.image);
  }
  const { data } = await api.patch<ProductItem>(`/products/${id}`, body);
  return data;
}

export async function fetchProductImage(id: number): Promise<string> {
  const { data, status } = await api.get<Blob>(`/products/${id}/image`, {
    responseType: "blob",
  });
  if (status !== 200 || !data.type.startsWith("image/")) {
    throw new Error("image");
  }
  return URL.createObjectURL(data);
}

export async function pauseProduct(id: number): Promise<ProductItem> {
  const { data } = await api.post<ProductItem>(`/products/${id}/pause`);
  return data;
}

export async function resumeProduct(id: number): Promise<ProductItem> {
  const { data } = await api.post<ProductItem>(`/products/${id}/resume`);
  return data;
}

export async function deleteProduct(id: number): Promise<void> {
  await api.delete(`/products/${id}`);
}

export async function askProductQuestion(
  productId: number,
  text: string,
): Promise<ProductQuestionItem> {
  const { data } = await api.post<ProductQuestionItem>(
    `/products/${productId}/questions`,
    { text },
  );
  return data;
}

export async function answerProductQuestion(
  questionId: number,
  text: string,
): Promise<ProductQuestionItem> {
  const { data } = await api.post<ProductQuestionItem>(
    `/questions/${questionId}/answers`,
    { text },
  );
  return data;
}

export async function listSellerQuestions(params?: {
  status?: SellerQuestionStatus;
  sort?: SellerQuestionSort;
  order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}): Promise<SellerQuestionListResult> {
  const { data } = await api.get<SellerQuestionListResult>("/questions", {
    params,
  });
  return data;
}

export async function listStores(params: {
  q?: string;
  page?: number;
  page_size?: number;
}): Promise<StoreListResult> {
  const { data } = await api.get<StoreListResult>("/stores", { params });
  return data;
}

export type Fulfillment = "envio" | "retiro";
export type PaymentMethod = "tarjeta" | "transferencia" | "efectivo";
export type SellStatus =
  | "en_carrito"
  | "en_curso"
  | "en_viaje"
  | "esperando_retiro"
  | "completada"
  | "cancelada"
  | "reembolsada";

export type SellItem = {
  id: number;
  product_id: number;
  product_name: string;
  store_name: string;
  buyer_email: string;
  seller_email: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
  fulfillment: Fulfillment;
  payment_method: PaymentMethod | null;
  status: SellStatus;
  checkout_id: string | null;
  eta_at: string | null;
  updated_at: string | null;
  can_manage: boolean;
};

export type SellMessageItem = {
  id: number;
  sell_id: number;
  sender_user_id: number;
  body: string;
  created_at: string;
  mine: boolean;
};

export type NotificationItem = {
  id: number;
  sell_id: number | null;
  product_id: number | null;
  kind: "mensaje" | "estado" | "pregunta" | "respuesta" | "venta";
  title: string;
  body: string;
  as_seller: boolean;
  read_at: string | null;
  created_at: string;
};

export type SellListResult = {
  items: SellItem[];
  total: number;
  page: number;
  page_size: number;
};

export async function addToCart(fields: {
  product_id: number;
  quantity: number;
  fulfillment: Fulfillment;
}): Promise<SellItem> {
  const { data } = await api.post<SellItem>("/sells", fields);
  return data;
}

export async function listSells(params: {
  status?: SellStatus;
  as_seller?: boolean;
  page?: number;
  page_size?: number;
}): Promise<SellListResult> {
  const { data } = await api.get<SellListResult>("/sells", { params });
  return data;
}

export async function patchSell(
  id: number,
  fields: { quantity?: number; fulfillment?: Fulfillment },
): Promise<SellItem> {
  const { data } = await api.patch<SellItem>(`/sells/${id}`, fields);
  return data;
}

export async function checkoutSells(fields: {
  payment_method: PaymentMethod;
  sell_ids?: number[];
  items?: {
    product_id: number;
    quantity: number;
    fulfillment: Fulfillment;
  }[];
}): Promise<SellListResult> {
  const { data } = await api.post<SellListResult>("/sells/checkout", fields);
  return data;
}

export async function transitionSell(
  id: number,
  status: SellStatus,
): Promise<SellItem> {
  const { data } = await api.post<SellItem>(`/sells/${id}/transition`, {
    status,
  });
  return data;
}

export async function getSell(id: number): Promise<SellItem> {
  const { data } = await api.get<SellItem>(`/sells/${id}`);
  return data;
}

export async function listSellMessages(
  id: number,
  params?: { page?: number; page_size?: number },
): Promise<{
  items: SellMessageItem[];
  total: number;
  page: number;
  page_size: number;
}> {
  const { data } = await api.get(`/sells/${id}/messages`, { params });
  return data;
}

export async function sendSellMessage(
  id: number,
  body: string,
): Promise<SellMessageItem> {
  const { data } = await api.post<SellMessageItem>(`/sells/${id}/messages`, {
    body,
  });
  return data;
}

export type DashboardDays = 7 | 30 | 90;

export type DashboardProduct = {
  product_id: number;
  name: string;
  units: number;
  amount: string;
  net_profit: string;
};

export type DashboardSeller = {
  email: string;
  sales_count: number;
  amount: string;
};

export type DashboardResult = {
  days: DashboardDays;
  from: string;
  sales_count: number;
  total_amount: string;
  net_profit_total: string;
  units_sold: number;
  average_ticket: string;
  open_orders: number;
  cancelled_count: number;
  refunded_count: number;
  refunded_amount: string;
  top_products: DashboardProduct[];
  sellers: DashboardSeller[];
};

export async function getDashboard(
  days: DashboardDays = 30,
): Promise<DashboardResult> {
  const { data } = await api.get<DashboardResult>("/dashboard", {
    params: { days },
  });
  return data;
}

export async function listNotifications(params?: {
  unread?: boolean;
  page?: number;
  page_size?: number;
}): Promise<{
  items: NotificationItem[];
  total: number;
  unread: number;
  page: number;
  page_size: number;
}> {
  const { data } = await api.get("/notifications", { params });
  return data;
}

export async function readNotification(
  id: number,
): Promise<NotificationItem> {
  const { data } = await api.post<NotificationItem>(
    `/notifications/${id}/read`,
  );
  return data;
}

export async function readAllNotifications(): Promise<void> {
  await api.post("/notifications/read-all");
}

export function getErrorDetail(error: unknown): string {
  if (
    axios.isAxiosError(error) &&
    typeof error.response?.data?.detail === "string"
  ) {
    return error.response.data.detail;
  }
  return "No se pudo completar la solicitud";
}
