import { redirect } from "next/navigation";

/**
 * ⚠️ A raiz "/" manda direto para /studio (o PROGRAMA).
 *
 * Antes a raiz servia a página de MARKETING do BlueBookStudio (abas
 * Studio 51 / MusicClipStudio / BlueBookStudio / Agente009). Quem abria o
 * app caía na página de vendas em vez do gerador de clipes — confusão
 * relatada pelo usuário em 20/09/2026.
 *
 * REDIRECT NO SERVIDOR (redirect() do next/navigation): acontece ANTES de
 * qualquer HTML chegar ao navegador. É redirect 307 de verdade, não depende
 * de JavaScript/hidratação. A versão anterior usava useEffect + router.replace
 * (client-side) e por isso era frágil: se o JS falhasse ou demorasse, a aba
 * aparecia com o título de marketing (herdado do layout raiz) e o usuário
 * tinha a impressão de estar na página de vendas.
 *
 * A landing continua disponível em /landing.
 */
export default function Home() {
  redirect("/studio");
}
