/**
 * Templates rápidos que o dashboard oferece.
 *
 * ⚠️ CORRIGIDO (06/10/2026): antes o dashboard tinha um `const TEMPLATES` local
 * e cada card linkava `/studio/new?template=<id>` — mas o wizard não lia esse
 * parâmetro (só `?novo=1` e `?projeto=<id>`). Resultado: o link não fazia
 * nada. O botão "Ver todos" também apontava pra `/studio/templates`, rota que
 * não existe (404).
 *
 * Agora: este módulo é compartilhado. O wizard (StudioClientShell) importa
 * `TEMPLATES` e `aplicarTemplate(id)` — clicar num card pré-preenche título,
 * descrição e formato do projeto. O link "Ver todos" foi removido.
 */

export interface TemplateDef {
  id: string;
  name: string;
  desc: string;
  tag: string;         // proporção exibida no badge (9:16, 16:9, 1:1)
  color: string;       // classe Tailwind do gradiente do card
  // Preset aplicado ao estado do wizard quando o template é escolhido:
  title: string;       // vira state.title
  theme: string;       // vira a descrição/prompts (state.descriptionHint)
  formato: "9/16" | "16/9" | "3/4" | "4/3" | "1/1";
  efeito_preferido: string;  // "ken_burns" | "fade" | "kinetic" — serve de dica p/ step 05
}

export const TEMPLATES: TemplateDef[] = [
  {
    id: "t1",
    name: "Épico Cinematográfico",
    desc: "Batidas fortes, estilo Vox Editorial",
    tag: "9:16",
    color: "from-neon/30 to-violet/20",
    title: "Épico Cinematográfico",
    theme: "Cenas amplas, lente grande-angular, paleta escura com destaque âmbar, movimento lento (Ken Burns). Estilo trailer.",
    formato: "9/16",
    efeito_preferido: "ken_burns",
  },
  {
    id: "t2",
    name: "Lo-fi Relaxante",
    desc: "Imagens calmas, tipografia arredondada",
    tag: "16:9",
    color: "from-ok/25 to-neon/15",
    title: "Lo-fi Relaxante",
    theme: "Planos fixos, transições suaves por fade, paleta pastel, tipografia arredondada; ritmo visual lento.",
    formato: "16/9",
    efeito_preferido: "fade",
  },
  {
    id: "t3",
    name: "Pop Animado",
    desc: "Transições rápidas, kinetic titles",
    tag: "9:16",
    color: "from-warn/30 to-err/15",
    title: "Pop Animado",
    theme: "Cortes secos no beat, tipografia cinética, cores saturadas, zoom punch nos refrões.",
    formato: "9/16",
    efeito_preferido: "kinetic",
  },
];

export function obterTemplate(id: string | null | undefined): TemplateDef | null {
  if (!id) return null;
  return TEMPLATES.find((t) => t.id === id) ?? null;
}
