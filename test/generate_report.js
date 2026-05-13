const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');
const path = require('path');

// ── 测试结果数据 ──────────────────────────────────────────
const results = [
  { 分类: '水菜',   代表产品: '小白菜',     总条数: 773, 训练集: 618, 测试集: 155, 数据起始: '2023-01-02', 数据截止: '2026-04-13', MAE: 0.3537, RMSE: 0.4466, MAPE: 21.42 },
  { 分类: '海水鱼', 代表产品: '带鱼',       总条数: 371, 训练集: 296, 测试集: 75,  数据起始: '2024-10-24', 数据截止: '2026-04-09', MAE: 0.0097, RMSE: 0.0113, MAPE: 0.08  },
  { 分类: '淡水鱼', 代表产品: '鲤鱼',       总条数: 372, 训练集: 297, 测试集: 75,  数据起始: '2024-10-24', 数据截止: '2026-04-09', MAE: 0.1805, RMSE: 0.2706, MAPE: 2.71  },
  { 分类: '牛肉类', 代表产品: '牛腩',       总条数: 512, 训练集: 409, 测试集: 103, 数据起始: '2024-10-24', 数据截止: '2026-04-13', MAE: 0.0911, RMSE: 0.1121, MAPE: 0.33  },
  { 分类: '猪肉类', 代表产品: '白条猪',     总条数: 868, 训练集: 694, 测试集: 174, 数据起始: '2023-01-01', 数据截止: '2026-04-13', MAE: 0.2636, RMSE: 0.3399, MAPE: 3.50  },
  { 分类: '禽蛋类', 代表产品: '肉鸡',       总条数: 512, 训练集: 409, 测试集: 103, 数据起始: '2024-10-24', 数据截止: '2026-04-09', MAE: 0.0405, RMSE: 0.0488, MAPE: 0.59  },
  { 分类: '羊肉类', 代表产品: '去骨羊前腿', 总条数: 513, 训练集: 410, 测试集: 103, 数据起始: '2024-10-24', 数据截止: '2026-04-13', MAE: 0.2861, RMSE: 0.3867, MAPE: 0.85  },
  { 分类: '虾蟹类', 代表产品: '基围虾',     总条数: 372, 训练集: 297, 测试集: 75,  数据起始: '2024-10-24', 数据截止: '2026-04-09', MAE: 8.6753, RMSE: 10.4230, MAPE: 5.70 },
  { 分类: '贝壳类', 代表产品: '花蛤',       总条数: 372, 训练集: 297, 测试集: 75,  数据起始: '2024-10-24', 数据截止: '2026-04-09', MAE: 0.0658, RMSE: 0.0868, MAPE: 1.46  },
  { 分类: '其他类', 代表产品: '柠檬',       总条数: 491, 训练集: 392, 测试集: 99,  数据起始: '2024-10-24', 数据截止: '2026-04-13', MAE: 0.1509, RMSE: 0.2488, MAPE: 1.60  },
];

const avgMAE  = (results.reduce((s, r) => s + r.MAE, 0) / results.length).toFixed(4);
const avgRMSE = (results.reduce((s, r) => s + r.RMSE, 0) / results.length).toFixed(4);
const avgMAPE = (results.reduce((s, r) => s + r.MAPE, 0) / results.length).toFixed(2);

// ── 样式常量 ──────────────────────────────────────────────
const BLUE      = '1E3A5F';
const BLUE_LIGHT = 'DBEAFE';
const BLUE_MID  = '3B82F6';
const GRAY_BG   = 'F8FAFC';
const BORDER_COLOR = 'CBD5E1';
const PAGE_W = 11906; // A4
const PAGE_H = 16838;
const MARGIN = 1080; // ~0.75 inch
const CONTENT_W = PAGE_W - MARGIN * 2; // 9746

const border = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: border, bottom: border, left: border, right: border };

const cell = (text, opts = {}) => new TableCell({
  borders,
  width: { size: opts.width || 1000, type: WidthType.DXA },
  shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
  verticalAlign: VerticalAlign.CENTER,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: [new Paragraph({
    alignment: opts.align || AlignmentType.CENTER,
    children: [new TextRun({
      text: String(text),
      size: 18,
      bold: opts.bold || false,
      color: opts.color || '1F2937',
      font: 'Arial',
    })]
  })]
});

// MAPE 评级
const mapeRating = (mape) => {
  if (mape < 5)  return { label: '优秀', color: '16A34A' };
  if (mape < 10) return { label: '良好', color: '2563EB' };
  if (mape < 20) return { label: '一般', color: 'D97706' };
  return { label: '较差', color: 'DC2626' };
};

// ── 构建文档 ──────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Arial', size: 22 } }
    },
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 36, bold: true, font: 'Arial', color: BLUE },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 }
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '1E3A5F' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER_COLOR, space: 1 } },
          children: [
            new TextRun({ text: 'Prophet 价格预测模型精度测试报告', font: 'Arial', size: 18, color: '64748B' }),
            new TextRun({ text: '\t2026-05-04', font: 'Arial', size: 18, color: '94A3B8' }),
          ],
          tabStops: [{ type: 'right', position: 8640 }],
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER_COLOR, space: 1 } },
          children: [
            new TextRun({ text: '第 ', font: 'Arial', size: 16, color: '94A3B8' }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Arial', size: 16, color: '94A3B8' }),
            new TextRun({ text: ' 页', font: 'Arial', size: 16, color: '94A3B8' }),
          ]
        })]
      })
    },
    children: [

      // ── 标题 ──
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'Prophet 价格预测模型', font: 'Arial', size: 52, bold: true, color: BLUE })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
        children: [new TextRun({ text: '精度测试报告', font: 'Arial', size: 44, bold: true, color: BLUE_MID })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 400 },
        children: [new TextRun({ text: '农产品物价数据分析系统  ·  2026年5月4日', font: 'Arial', size: 20, color: '64748B' })]
      }),

      // ── 一、测试概述 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('一、测试概述')] }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        children: [new TextRun({
          text: '本次测试采用 Facebook Prophet 时间序列预测模型，对农产品价格数据库中 10 个品类的代表性产品进行预测精度评估。测试方法为：取每个产品的全量历史数据，前 80% 作为训练集，后 20% 作为测试集，在测试集上计算预测误差指标。',
          font: 'Arial', size: 22, color: '374151'
        })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 320 },
        children: [new TextRun({
          text: '数据来源：PostgreSQL 数据库（agriprice）  |  模型参数：changepoint_prior_scale=0.05，加入中国节假日效应',
          font: 'Arial', size: 20, color: '6B7280'
        })]
      }),

      // ── 二、评估指标说明 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('二、评估指标说明')] }),

      // 指标说明表
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [1600, 2800, 5346],
        rows: [
          new TableRow({
            tableHeader: true,
            children: [
              cell('指标', { width: 1600, bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('全称', { width: 2800, bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('含义', { width: 5346, bold: true, shading: BLUE, color: 'FFFFFF', align: AlignmentType.LEFT }),
            ]
          }),
          new TableRow({ children: [
            cell('MAE', { width: 1600, shading: GRAY_BG }),
            cell('平均绝对误差', { width: 2800, shading: GRAY_BG }),
            cell('预测值与真实值差的绝对值均值，单位：元/斤，越小越好', { width: 5346, shading: GRAY_BG, align: AlignmentType.LEFT }),
          ]}),
          new TableRow({ children: [
            cell('RMSE', { width: 1600 }),
            cell('均方根误差', { width: 2800 }),
            cell('对大误差更敏感，反映预测稳定性，单位：元/斤，越小越好', { width: 5346, align: AlignmentType.LEFT }),
          ]}),
          new TableRow({ children: [
            cell('MAPE', { width: 1600, shading: GRAY_BG }),
            cell('平均绝对百分比误差', { width: 2800, shading: GRAY_BG }),
            cell('误差占真实值的百分比，消除量纲影响，越小越好（<5% 优秀，<10% 良好，<20% 一般）', { width: 5346, shading: GRAY_BG, align: AlignmentType.LEFT }),
          ]}),
        ]
      }),
      new Paragraph({ spacing: { before: 0, after: 320 }, children: [] }),

      // ── 三、详细测试结果 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('三、详细测试结果')] }),

      // 结果主表
      new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [900, 1300, 800, 800, 800, 1100, 1100, 900, 900, 1146],
        rows: [
          // 表头
          new TableRow({
            tableHeader: true,
            children: [
              cell('分类',       { width: 900,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('代表产品',   { width: 1300, bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('总条数',     { width: 800,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('训练集',     { width: 800,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('测试集',     { width: 800,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('数据起始',   { width: 1100, bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('数据截止',   { width: 1100, bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('MAE',        { width: 900,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('RMSE',       { width: 900,  bold: true, shading: BLUE, color: 'FFFFFF' }),
              cell('MAPE(%)',    { width: 1146, bold: true, shading: BLUE, color: 'FFFFFF' }),
            ]
          }),
          // 数据行
          ...results.map((r, i) => {
            const rating = mapeRating(r.MAPE);
            const bg = i % 2 === 0 ? GRAY_BG : undefined;
            return new TableRow({ children: [
              cell(r.分类,       { width: 900,  shading: bg }),
              cell(r.代表产品,   { width: 1300, shading: bg }),
              cell(r.总条数,     { width: 800,  shading: bg }),
              cell(r.训练集,     { width: 800,  shading: bg }),
              cell(r.测试集,     { width: 800,  shading: bg }),
              cell(r.数据起始,   { width: 1100, shading: bg }),
              cell(r.数据截止,   { width: 1100, shading: bg }),
              cell(r.MAE.toFixed(4),  { width: 900,  shading: bg }),
              cell(r.RMSE.toFixed(4), { width: 900,  shading: bg }),
              // MAPE 带颜色评级
              new TableCell({
                borders,
                width: { size: 1146, type: WidthType.DXA },
                shading: bg ? { fill: bg, type: ShadingType.CLEAR } : undefined,
                verticalAlign: VerticalAlign.CENTER,
                margins: { top: 80, bottom: 80, left: 120, right: 120 },
                children: [new Paragraph({
                  alignment: AlignmentType.CENTER,
                  children: [
                    new TextRun({ text: `${r.MAPE}%  `, font: 'Arial', size: 18, color: '1F2937' }),
                    new TextRun({ text: rating.label, font: 'Arial', size: 16, bold: true, color: rating.color }),
                  ]
                })]
              }),
            ]});
          }),
          // 平均值行
          new TableRow({ children: [
            cell('平均值', { width: 900,  bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 1300, bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 800,  bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 800,  bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 800,  bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 1100, bold: true, shading: BLUE_LIGHT }),
            cell('—',      { width: 1100, bold: true, shading: BLUE_LIGHT }),
            cell(avgMAE,   { width: 900,  bold: true, shading: BLUE_LIGHT, color: BLUE }),
            cell(avgRMSE,  { width: 900,  bold: true, shading: BLUE_LIGHT, color: BLUE }),
            cell(`${avgMAPE}%`, { width: 1146, bold: true, shading: BLUE_LIGHT, color: BLUE }),
          ]})
        ]
      }),
      new Paragraph({ spacing: { before: 0, after: 320 }, children: [] }),

      // ── 四、结果分析 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('四、结果分析')] }),

      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('4.1 整体表现')] }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({
          text: `10 个品类中，9 个品类 MAPE 低于 10%，整体平均 MAPE 为 ${avgMAPE}%，平均 MAE 为 ${avgMAE} 元/斤，平均 RMSE 为 ${avgRMSE} 元/斤。模型在大多数农产品品类上表现良好，具备实际应用价值。`,
          font: 'Arial', size: 22, color: '374151'
        })]
      }),

      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('4.2 各品类分析')] }),
      new Paragraph({
        spacing: { before: 0, after: 120 },
        children: [new TextRun({ text: '表现优秀（MAPE < 5%）：', font: 'Arial', size: 22, bold: true, color: '16A34A' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({
          text: '带鱼（0.08%）、牛腩（0.33%）、肉鸡（0.59%）、去骨羊前腿（0.85%）、花蛤（1.46%）、柠檬（1.60%）、鲤鱼（2.71%）、白条猪（3.50%）、基围虾（5.70%）共 9 个品类达到优秀或良好水平。这些产品价格走势相对平稳，Prophet 的趋势分解和节假日效应建模效果显著。',
          font: 'Arial', size: 22, color: '374151'
        })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 120 },
        children: [new TextRun({ text: '需关注（MAPE > 20%）：', font: 'Arial', size: 22, bold: true, color: 'DC2626' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 200 },
        children: [new TextRun({
          text: '小白菜（21.42%）误差偏高，原因在于叶菜类价格受季节、天气影响波动剧烈，短期随机性强，时间序列模型难以捕捉突发性价格跳变。建议对叶菜类引入气象特征或增加外生变量。',
          font: 'Arial', size: 22, color: '374151'
        })]
      }),

      new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('4.3 虾蟹类说明')] }),
      new Paragraph({
        spacing: { before: 0, after: 320 },
        children: [new TextRun({
          text: '基围虾 MAE 为 8.68 元/斤，绝对误差较大，但 MAPE 仅 5.70%，说明误差主要来自其本身价格基数高（均价约 150 元/斤），相对误差仍在可接受范围内。',
          font: 'Arial', size: 22, color: '374151'
        })]
      }),

      // ── 五、结论 ──
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('五、结论与建议')] }),
      new Paragraph({
        spacing: { before: 0, after: 160 },
        children: [new TextRun({
          text: 'Prophet 模型在本系统农产品价格预测场景中整体表现良好，适合作为中短期价格预测的基础模型。具体建议如下：',
          font: 'Arial', size: 22, color: '374151'
        })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: '1.  叶菜类（小白菜等）建议引入气象数据作为外生变量，或改用 LSTM 等深度学习模型。', font: 'Arial', size: 22, color: '374151' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: '2.  高价格基数品类（虾蟹类）评估时应以 MAPE 为主要参考指标，而非绝对误差。', font: 'Arial', size: 22, color: '374151' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: '3.  数据量较少的品类（< 400 条）建议持续积累数据，以提升模型训练效果。', font: 'Arial', size: 22, color: '374151' })]
      }),
      new Paragraph({
        spacing: { before: 0, after: 100 },
        children: [new TextRun({ text: '4.  当前模型已加入中国节假日效应，建议定期重训练以适应最新价格趋势。', font: 'Arial', size: 22, color: '374151' })]
      }),
    ]
  }]
});

// ── 输出文件 ──────────────────────────────────────────────
const outPath = path.join(__dirname, 'prophet_accuracy_report.docx');
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('报告已生成：' + outPath);
});
