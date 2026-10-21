import { test, expect } from "@playwright/test";

test("DOI, investigação, evidência, camadas, lista e exportação", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Toda descoberta/ }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/inicio.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Edição genômica/ }).click();
  await expect(
    page.getByRole("heading", {
      name: "Multiplex Genome Engineering Using CRISPR/Cas Systems",
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Investigar contribuições femininas" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Explore o conhecimento. Siga as evidências.",
    }),
  ).toBeVisible();
  await page
    .locator(".discovery-card")
    .filter({ hasText: "Cas9 programável" })
    .click();
  await expect(page.locator(".dossier")).toContainText("Jennifer A. Doudna");
  await expect(page.locator(".dossier")).toContainText(
    "Emmanuelle Charpentier",
  );
  await expect(page.locator(".dossier")).toContainText("Citação identificada");
  await expect(page.locator(".source-card a")).toHaveAttribute(
    "href",
    "https://doi.org/10.1126/science.1225829",
  );
  await expect(page.locator(".react-flow__node").first()).toHaveCSS(
    "visibility",
    "visible",
  );
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);
  await page.screenshot({
    path: "../docs/screenshots/investigacao.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Bibliografia", exact: true }).click();
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await page
    .getByRole("button", { name: "Contribuições", exact: true })
    .click();
  await page.getByRole("button", { name: "Lista", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Relações da investigação" }),
  ).toBeVisible();
  await expect(page.locator(".text-results")).toContainText("Relação temática");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Dossiê .md" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/matilda-.*\.md/);
  expect(errors).toEqual([]);
});

test("cenário RNA e navegação mobile sem depender do grafo", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: /Vacinas de RNA/ }).click();
  await page
    .getByRole("button", { name: "Investigar contribuições femininas" })
    .click();
  await expect(page.locator(".discovery-card")).toHaveCount(2);
  await page.locator(".discovery-card").first().click();
  await expect(page.locator(".dossier")).toContainText("Katalin Karikó");
  await expect(page.locator(".source-card a")).toHaveAttribute(
    "href",
    /https:\/\/doi.org\//,
  );
  await page.screenshot({
    path: "../docs/screenshots/mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Grafo e lista" }).click();
  await page.getByRole("button", { name: "Lista", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Relações da investigação" }),
  ).toBeVisible();
});

test("DOI inválido e ausência de cobertura sem resultados inventados", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("COMECE POR UM ARTIGO CIENTÍFICO").fill("não-é-doi");
  await page.getByRole("button", { name: "Recuperar artigo por DOI" }).click();
  await expect(page.getByRole("alert")).toContainText("DOI inválido");
  await page
    .getByLabel("COMECE POR UM ARTIGO CIENTÍFICO")
    .fill("10.1038/171737a0");
  await page.getByRole("button", { name: "Recuperar artigo por DOI" }).click();
  await page
    .getByRole("button", { name: "Investigar contribuições femininas" })
    .click();
  await expect(
    page.getByRole("heading", { name: "Sem correspondência no catálogo" }),
  ).toBeVisible();
  await expect(page.locator(".empty-result")).toContainText(
    "não indica ausência",
  );
});

test("busca e descoberta por teclado", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("COMECE POR UM ARTIGO CIENTÍFICO").focus();
  await page.keyboard.type("10.1126/science.1231143");
  await page.keyboard.press("Enter");
  const investigate = page.getByRole("button", {
    name: "Investigar contribuições femininas",
  });
  await investigate.focus();
  await page.keyboard.press("Enter");
  const first = page.locator(".discovery-card").first();
  await expect(first).toBeVisible();
  await first.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".dossier .source-card a")).toBeVisible();
  await page.getByRole("button", { name: "Lista", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("heading", { name: "Relações da investigação" }),
  ).toBeVisible();
});
