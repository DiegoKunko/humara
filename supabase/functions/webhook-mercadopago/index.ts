import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const MP_ACCESS_TOKEN = Deno.env.get("MERCADOPAGO_ACCESS_TOKEN")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

serve(async (req) => {
  // MercadoPago sends GET for topic-based notifications
  // and POST for webhook notifications
  try {
    const url = new URL(req.url);
    const topic = url.searchParams.get("topic") || url.searchParams.get("type");
    const resourceId = url.searchParams.get("id");

    let paymentId: string | null = null;

    if (req.method === "POST") {
      const body = await req.json();
      // IPN v2 format
      if (body.type === "payment" && body.data?.id) {
        paymentId = String(body.data.id);
      }
      // IPN v1 format
      if (body.topic === "payment" && body.resource) {
        const parts = body.resource.split("/");
        paymentId = parts[parts.length - 1];
      }
    }

    // GET-based notification
    if (!paymentId && topic === "payment" && resourceId) {
      paymentId = resourceId;
    }

    if (!paymentId) {
      // Not a payment notification, acknowledge
      return new Response("OK", { status: 200 });
    }

    // Verify payment with MercadoPago
    const mpRes = await fetch(
      `https://api.mercadopago.com/v1/payments/${paymentId}`,
      {
        headers: { Authorization: `Bearer ${MP_ACCESS_TOKEN}` },
      }
    );

    if (!mpRes.ok) {
      console.error("MP verification failed:", mpRes.status);
      return new Response("MP error", { status: 502 });
    }

    const payment = await mpRes.json();
    const orderId = payment.external_reference;

    if (!orderId) {
      console.error("No external_reference in payment");
      return new Response("OK", { status: 200 });
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    if (payment.status === "approved") {
      await supabase
        .from("orders")
        .update({
          status: "paid",
          payment_id: String(paymentId),
          paid_at: new Date().toISOString(),
        })
        .eq("id", orderId);

      console.log(`Order ${orderId} marked as paid (payment ${paymentId})`);
    } else if (payment.status === "rejected" || payment.status === "cancelled") {
      await supabase
        .from("orders")
        .update({
          status: "pending_payment",
          error_message: `Payment ${payment.status}: ${payment.status_detail || ""}`,
        })
        .eq("id", orderId);
    }

    return new Response("OK", { status: 200 });
  } catch (err) {
    console.error("Webhook error:", err);
    return new Response("Error", { status: 500 });
  }
});
