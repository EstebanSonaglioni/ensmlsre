import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProductList } from "@/app/product-list";
import type { ProductItem } from "@/lib/api";

const { listProducts, listMyProducts, fetchProductImage } = vi.hoisted(() => ({
  listProducts: vi.fn(),
  listMyProducts: vi.fn(),
  fetchProductImage: vi.fn(),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    listProducts,
    listMyProducts,
    fetchProductImage,
  };
});

function product(overrides: Partial<ProductItem> = {}): ProductItem {
  return {
    id: 1,
    store_id: 1,
    store_name: "Demo Store",
    name: "Notebook",
    quantity: 3,
    price: "1200.00",
    category: "Tec",
    subcategory: "PC",
    paused: false,
    ships: true,
    pickup: true,
    ...overrides,
  };
}

describe("ProductList", () => {
  beforeEach(() => {
    listProducts.mockReset();
    listMyProducts.mockReset();
    fetchProductImage.mockRejectedValue(new Error("sin imagen"));
  });

  it("lista productos del catálogo", async () => {
    listProducts.mockResolvedValue({
      items: [product()],
      total: 1,
      page: 1,
      page_size: 10,
    });

    render(<ProductList refreshKey={0} />);

    expect(screen.getByText("Cargando...")).toBeInTheDocument();
    expect(await screen.findByText("Notebook")).toBeInTheDocument();
    expect(screen.getByText("$ 1200.00")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Notebook/ })).toHaveAttribute(
      "href",
      "/productos/1",
    );
    expect(listMyProducts).not.toHaveBeenCalled();
  });

  it("muestra vacío cuando no hay publicaciones", async () => {
    listProducts.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    });

    render(<ProductList refreshKey={0} />);

    expect(
      await screen.findByText("No hay publicaciones para mostrar."),
    ).toBeInTheDocument();
  });

  it("muestra el detail genérico si falla el listado", async () => {
    listProducts.mockRejectedValue(new Error("red"));

    render(<ProductList refreshKey={0} />);

    expect(
      await screen.findByText("No se pudo completar la solicitud"),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByText("Cargando...")).not.toBeInTheDocument();
    });
  });

  it("en modo mine pide publicaciones propias y no el buscador", async () => {
    listMyProducts.mockResolvedValue({
      items: [product({ name: "Mía" })],
      total: 1,
      page: 1,
      page_size: 10,
    });

    render(<ProductList refreshKey={0} mine />);

    expect(await screen.findByText("Tus publicaciones")).toBeInTheDocument();
    expect(screen.getByText("Mía")).toBeInTheDocument();
    expect(
      screen.queryByRole("searchbox", { name: "Buscar por nombre" }),
    ).not.toBeInTheDocument();
    expect(listProducts).not.toHaveBeenCalled();
  });
});
