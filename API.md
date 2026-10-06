# API — IDENTIFY 2.0 backend

Contrato para quem vai consumir a API no frontend.

> ## Leia isto antes de desenhar a tela
>
> **O modelo detecta a presença de agave. Ele NÃO diagnostica doença.**
>
> Uma caixa na imagem significa "existe uma planta de agave aqui" — nada mais.
> O modelo tem uma classe só (`agave`) e não distingue planta doente de sadia.
>
> A classificação de podridão vermelha é a **etapa 2** do projeto, ainda em
> desenvolvimento. Enquanto ela não existir, nenhum texto da interface deve
> dizer "doente", "sadia", "podridão", "diagnóstico" ou "%" de doença com base
> nesta resposta.
>
> Sugestão de rótulo honesto: *"N plantas de agave detectadas"*.
>
> Detalhes e limitações em [`models/MODELO.md`](models/MODELO.md).

---

## `GET /health`

```json
{ "status": "online", "message": "Backend do IDENTIFY 2.0 ativo." }
```

## `POST /api/analyze`

Uma imagem por requisição. `multipart/form-data`, campo **`file`**.

```js
const formData = new FormData();
formData.append("file", arquivo);
const resp = await fetch("/api/analyze", { method: "POST", body: formData });
const data = await resp.json();
```

### Resposta `200`

```json
{
  "filename": "DJI_0990.JPG",
  "content_type": "image/jpeg",
  "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
  "total_agaves": 678,
  "largura": 5472,
  "altura": 3078,
  "conf": 0.3,
  "avisos": []
}
```

| Campo | Tipo | O que é |
|---|---|---|
| `filename` | string | o nome que veio no upload |
| `content_type` | string | o MIME que veio no upload |
| `image_data` | string | **data-URI pronto para `<img src>`**: a imagem original com as caixas desenhadas, já em base64 |
| `total_agaves` | int | quantas plantas foram detectadas |
| `largura`, `altura` | int | dimensões da imagem enviada, em pixels |
| `conf` | float | limiar de confiança usado (ver abaixo) |
| `avisos` | string[] | **se não estiver vazio, mostre ao usuário** (ver abaixo) |

O `image_data` já serve tanto para exibir quanto para o botão de download:

```js
const link = document.createElement("a");
link.href = data.image_data;
link.download = `agaves_${data.filename}`;
link.click();
```

### Erros

| Código | Quando | `detail` |
|---|---|---|
| `400` | não é imagem, arquivo vazio, ou imagem corrompida | mensagem em português, exibível |
| `422` | o campo `file` não foi enviado | formato padrão do FastAPI |
| `500` | falha inesperada no processamento | mensagem genérica |

O corpo do erro é `{ "detail": "..." }`. As mensagens de `400` são escritas para
serem mostradas ao usuário direto.

---

## Três coisas que vão afetar a sua tela

### 1. Demora ~11 segundos por imagem

Não é exagero nem bug: a imagem de drone é recortada em 45 pedaços e cada um
passa pelo modelo. Medido em CPU de 12 núcleos.

Consequências:

- **Precisa de estado de carregamento.** 11 segundos sem retorno visual parece
  travamento.
- **Com várias fotos, multiplica.** 10 fotos = ~2 minutos. Envie uma por
  requisição, em sequência, e mostre o progresso por foto (`3 de 10`) em vez de
  uma barra única. Não dispare as 10 em paralelo: o servidor processa uma por
  vez de qualquer forma (há uma trava interna), então o paralelismo só faria
  todas estourarem o timeout juntas.
- **Cuidado com o timeout** do `fetch`, do proxy e do gateway. 11s por imagem já
  passa do padrão de alguns.

### 2. A resposta pesa ~7,6 MB por imagem

O `image_data` é a imagem em resolução original (5472×3078) embutida em base64,
o que infla o tamanho em ~33%.

- Em localhost é instantâneo. Pela internet, não.
- Não guarde muitas dessas strings em memória no navegador: 10 fotos = ~76 MB
  de JavaScript heap.
- Se isso virar problema, fale com o backend: a alternativa é a API salvar a
  imagem e devolver uma URL. Muda o contrato, então é conversa, não ajuste.

### 3. O campo `avisos` não é decorativo

Hoje existe um aviso, e ele importa: **imagem redimensionada**.

O modelo foi treinado em fotos de 5472×3078, onde a planta tem ~130px. Se a
imagem chegar reduzida, as plantas ficam pequenas demais e a detecção despenca
— **sem gerar erro nenhum**:

| Imagem enviada | Plantas detectadas |
|---|---|
| 5472×3078 (original do drone) | **678** |
| 1600×900 (redimensionada) | **321** |

Metade desaparece silenciosamente. Então:

- **Não redimensione nem recomprima a imagem no frontend antes de enviar.**
  Mande o arquivo original do drone.
- Se `avisos` vier preenchido, mostre o texto. Ele já vem escrito em português
  e explica o que o usuário deve fazer.

---

## Sobre o `conf`

É o limiar de confiança. Está fixo em **0,30** no servidor, e esse valor foi
escolhido medindo:

| conf | Plantas achadas | Caixas erradas | Erro na contagem |
|---|---|---|---|
| 0,20 | 87% | muitas | +27,8% |
| **0,30** | 81% | moderadas | **+4,9%** |
| 0,40 | 72% | poucas | −12,8% |

Em 0,30 as caixas sobrando quase compensam as plantas perdidas, e a **contagem
exibida erra menos de 5%**. É por isso que ele é o padrão, e é por isso que o
número em `total_agaves` pode ser apresentado como estimativa de contagem.

O campo vem na resposta para registro; o frontend não escolhe o valor.

---

## Honestidade sobre a precisão

Os números acima foram medidos em **2 imagens de validação** (756 plantas
contadas à mão). São honestos, mas é uma amostra pequena: não trate o erro de
4,9% como garantia num voo novo, e evite exibir a contagem sem a palavra
"aproximadamente".

O modelo foi treinado numa plantação específica, com um drone específico. Em
outro sítio ou outra câmera, o desempenho cai.
