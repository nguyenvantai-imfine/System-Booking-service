import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const sourcePath = new URL("../src/index.ts", import.meta.url);
const source = readFileSync(sourcePath, "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
  },
});

function createRequest(
  getAuthToken,
  response = {
    ok: true,
    status: 200,
    json: async () => ({ items: [], total: 0, page: 1, page_size: 20, total_pages: 0 }),
  },
  operation = (client) => client.getHotels(),
) {
  let authorization;
  let requestUrl;
  const module = { exports: {} };
  const sandbox = {
    module,
    exports: module.exports,
    URLSearchParams,
    require: (specifier) => {
      if (specifier === "@repo/types") return {};
      throw new Error(`Unexpected runtime dependency: ${specifier}`);
    },
    fetch: async (url, options) => {
      requestUrl = url;
      authorization = options.headers.Authorization;
      return response;
    },
  };

  vm.runInNewContext(outputText, sandbox, { filename: "api-client.js" });
  const client = module.exports.createApiClient({
    baseUrl: "http://localhost:8080/api/v1",
    getAuthToken,
  });

  return {
    request: operation(client),
    getAuthorization: () => authorization,
    getUrl: () => requestUrl,
  };
}

test("does not send a fabricated Authorization header without a token provider", async () => {
  const request = createRequest(undefined);
  await request.request;
  assert.equal(request.getAuthorization(), undefined);
});

test("does not send an Authorization header when the token provider is empty", async () => {
  const request = createRequest(() => null);
  await request.request;
  assert.equal(request.getAuthorization(), undefined);
});

test("sends a bearer header when a JWT is available", async () => {
  const request = createRequest(() => "valid-jwt-token");
  await request.request;
  assert.equal(request.getAuthorization(), "Bearer valid-jwt-token");
});

test("reports a useful API error when the gateway returns plain text", async () => {
  const request = createRequest(undefined, {
    ok: false,
    status: 502,
    text: async () => "upstream unavailable",
  });
  await assert.rejects(
    request.request,
    (error) => {
      assert.equal(error.name, "ApiError");
      assert.equal(error.statusCode, 502);
      assert.equal(error.message, "upstream unavailable");
      return true;
    },
  );
});

test("sends the Booking API's id_khach_san hotel filter", async () => {
  const request = createRequest(
    undefined,
    undefined,
    (client) => client.getBookings({ hotel_id: 42 }),
  );
  await request.request;
  const url = new URL(request.getUrl());
  assert.equal(url.searchParams.get("id_khach_san"), "42");
  assert.equal(url.searchParams.has("hotel_id"), false);
});

test("keeps the Room API's hotel_id filter", async () => {
  const request = createRequest(
    undefined,
    undefined,
    (client) => client.getRooms({ hotel_id: 42 }),
  );
  await request.request;
  const url = new URL(request.getUrl());
  assert.equal(url.searchParams.get("hotel_id"), "42");
  assert.equal(url.searchParams.has("id_khach_san"), false);
});

test("does not send an unsupported cancellation reason query", async () => {
  const request = createRequest(
    undefined,
    undefined,
    (client) => client.cancelBooking(42),
  );
  await request.request;
  const url = new URL(request.getUrl());
  assert.equal(url.pathname, "/api/v1/bookings/42/cancel");
  assert.equal(url.searchParams.has("reason"), false);
});
