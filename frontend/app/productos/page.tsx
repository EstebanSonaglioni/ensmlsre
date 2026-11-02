"use client";

import { useState } from "react";

import { AuthGate } from "@/components/auth-gate";

import { CreateProductForm } from "../create-product-form";
import { ProductList } from "../product-list";

export default function ProductosPage() {
  const [productVersion, setProductVersion] = useState(0);

  return (
    <AuthGate sellerOnly>
      {() => (
        <>
          <CreateProductForm
            refreshKey={0}
            onCreated={() => setProductVersion((value) => value + 1)}
          />
          <ProductList refreshKey={productVersion} mine />
        </>
      )}
    </AuthGate>
  );
}
