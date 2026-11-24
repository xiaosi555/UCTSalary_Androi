from pathlib import Path
import json
import sys

root = Path(sys.argv[1])

def replace_once(path: str, old: str, new: str):
    p = root / path
    s = p.read_text(encoding='utf-8')
    if old not in s:
        raise SystemExit(f'PATCH FAILED: expected block not found in {path}')
    p.write_text(s.replace(old, new, 1), encoding='utf-8')
    print(f'PATCHED {path}')

def replace_region(path: str, start_marker: str, end_marker: str, replacement: str):
    p = root / path
    s = p.read_text(encoding='utf-8')
    start = s.find(start_marker)
    if start < 0:
        raise SystemExit(f'PATCH FAILED: start marker not found in {path}: {start_marker}')
    end = s.find(end_marker, start + len(start_marker))
    if end < 0:
        raise SystemExit(f'PATCH FAILED: end marker not found in {path}: {end_marker}')
    p.write_text(s[:start] + replacement + s[end:], encoding='utf-8')
    print(f'PATCHED {path}')

replace_once(
    'app/src/main/java/com/uct/salary/core/Calc.kt',
    '''        val sub = subsidyAt(history, key)
        return Summary(
            base = cfg.base,
            ot = ot,
            night = subsidyValue(subsidyByName(sub, "夜班补贴"), key),
            meal = subsidyValue(subsidyByName(sub, "伙食补贴"), key),
            taxable = cfg.tax,
            social = cfg.social
        )''',
    '''        val sub = subsidyAt(history, key)
        // 与原版 HTML computeCycleSummary 一致：应纳税所得额不是个人所得税金额。
        val subAll = sub.sumOf { subsidyValue(it, key) }
        val taxableIncome = max(0.0, cfg.base + ot + subAll - cfg.social - cfg.housing - 5000.0)
        return Summary(
            base = cfg.base,
            ot = ot,
            night = subsidyValue(subsidyByName(sub, "夜班补贴"), key),
            meal = subsidyValue(subsidyByName(sub, "伙食补贴"), key),
            taxable = taxableIncome,
            social = cfg.social
        )'''
)


replace_once(
    'app/src/main/java/com/uct/salary/core/Calc.kt',
    """    fun ratesAt(history: List<SettingsVersion>, key: String): Rates {
        val l = sorted(history).filter { it.from <= key }
        for (i in l.indices.reversed()) {
            val r = l[i].deduction.rates
            if (r != null) return r
        }
        return Rates()
    }""",
    """    fun ratesAt(history: List<SettingsVersion>, key: String): Rates {
        // 原版 HTML 的五险比例来自当前设置项，历史快照只保存缴费基数。
        return sorted(history).asReversed().firstNotNullOfOrNull { it.deduction.rates } ?: Rates()
    }"""
)

replace_once(
    'app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt',
    '''    var modifier = Modifier.fillMaxWidth().height(56.dp).clip(shape)
    modifier = when {
        isToday -> modifier.background(pri.copy(alpha = 0.2f)).border(2.dp, pri, shape)
        isNight -> modifier.background(Gray100.copy(alpha = 0.6f)).border(1.dp, pri, shape)
        else -> modifier.background(Gray100.copy(alpha = 0.6f))
    }
    Box(modifier.clickable(onClick = onClick).padding(3.dp)) {
        Text(d.dayOfMonth.toString(), fontSize = 11.sp, color = Gray900, modifier = Modifier.align(Alignment.TopStart))''',
    '''    val modifier = Modifier.fillMaxWidth().height(56.dp).clip(shape)
    val cellSurface = when {
        isToday -> modifier.background(pri.copy(alpha = 0.2f)).border(2.dp, pri, shape)
        isNight -> modifier.background(White).border(1.dp, pri, shape)
        else -> modifier.background(White).border(1.dp, Gray200, shape)
    }
    Box(cellSurface.clickable(onClick = onClick).padding(3.dp)) {
        Text(d.dayOfMonth.toString(), fontSize = 11.sp, color = Gray400, modifier = Modifier.align(Alignment.TopStart))'''
)
replace_once('app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt', "else -> Gray800\n    }", "else -> pri\n    }")
replace_once('app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt', 'modifier = Modifier.align(Alignment.Center))', 'modifier = Modifier.align(Alignment.CenterEnd))')
replace_once('app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt', 'val shape = RoundedCornerShape(8.dp)', 'val shape = RoundedCornerShape(6.dp)')
replace_once(
    'app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt',
    '''            Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp)) {
                WEEK_HEAD.forEach {
                    Text(it, Modifier.weight(1f), fontSize = 12.sp, color = Gray500, textAlign = TextAlign.Center)
                }
            }''',
    '''            Row(Modifier.fillMaxWidth().background(Gray100.copy(alpha = 0.45f)).padding(horizontal = 8.dp, vertical = 10.dp)) {
                WEEK_HEAD.forEach {
                    Text(it, Modifier.weight(1f), fontSize = 12.sp, color = Gray400, textAlign = TextAlign.Center)
                }
            }'''
)
replace_once(
    'app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt',
    '''            SummaryBox(vm, key, Modifier.padding(horizontal = 12.dp))
            Spacer(Modifier.height(24.dp))''',
    '''            Column(Modifier.fillMaxWidth().background(Gray100.copy(alpha = 0.55f)).padding(horizontal = 12.dp, vertical = 12.dp)) {
                SummaryBox(vm, key)
            }
            Spacer(Modifier.height(24.dp))'''
)
replace_region(
    'app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt',
    '@Composable\nprivate fun SummaryBox(',
    '\n}',
    '''@Composable
private fun SummaryBox(vm: AppViewModel, key: String, modifier: Modifier = Modifier) {
    val s = remember(vm.data.records, vm.data.history, key) { Calc.summary(vm.data.records, vm.data.history, key) }
    val v = vm.data.summaryVisible
    data class Item(val label: String, val value: Double, val sign: Int, val visible: Boolean?, val toggle: () -> Unit)

    val items = listOf(
        Item("基本工资", s.base, 1, null) {},
        Item("加班工资", s.ot, 1, null) {},
        Item("夜班补贴", s.night, 1, v.night) { vm.setSummaryVisible(v.copy(night = !v.night)) },
        Item("餐补", s.meal, 1, v.meal) { vm.setSummaryVisible(v.copy(meal = !v.meal)) },
        Item("应纳税所得额", s.taxable, -1, v.taxable) { vm.setSummaryVisible(v.copy(taxable = !v.taxable)) },
        Item("个人五险", s.social, -1, v.social) { vm.setSummaryVisible(v.copy(social = !v.social)) }
    )
    val total = items.sumOf { if (it.visible != false) it.sign * it.value else 0.0 }

    CardBox(modifier, padding = 0.dp) {
        Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("收支汇总", fontSize = 15.sp, fontWeight = FontWeight.Medium, color = Gray800, modifier = Modifier.weight(1f))
            Text(
                "查看统计 ›", fontSize = 12.sp, color = primary(),
                modifier = Modifier.clip(RoundedCornerShape(6.dp)).background(primary().copy(alpha = 0.10f))
                    .clickable { vm.openStats(0, keepCycle = true) }.padding(horizontal = 8.dp, vertical = 5.dp)
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(Gray100))
        items.chunked(2).forEach { pair ->
            Row(Modifier.fillMaxWidth()) {
                pair.forEachIndexed { index, item ->
                    Column(Modifier.weight(1f).padding(horizontal = 16.dp, vertical = 12.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(item.label, fontSize = 12.sp, color = Gray400)
                            if (item.visible != null) {
                                Spacer(Modifier.width(4.dp))
                                EyeButton(item.visible, item.toggle, size = 16.dp)
                            }
                        }
                        val shown = item.visible != false
                        Text(
                            Fmt.money(item.value), fontSize = 16.sp, fontWeight = FontWeight.Medium,
                            color = if (shown) Gray800 else Gray400,
                            textDecoration = if (shown) null else TextDecoration.LineThrough
                        )
                    }
                    if (index == 0 && pair.size > 1) Spacer(Modifier.width(1.dp).height(54.dp).background(Gray100))
                }
            }
            Box(Modifier.fillMaxWidth().height(1.dp).background(Gray100))
        }
        Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("合计", fontSize = 14.sp, color = Gray800, modifier = Modifier.weight(1f))
            Text(Fmt.money(total), fontSize = 18.sp, fontWeight = FontWeight.Bold, color = primary())
        }
    }'''
)

replace_region(
    'app/src/main/java/com/uct/salary/ui/screens/HomeScreen.kt',
    '@Composable\nfun HomeScreen(vm: AppViewModel) {',
    '\n@Composable\nprivate fun HomeEntry',
    '''@Composable
fun HomeScreen(vm: AppViewModel) {
    val key = Dates.realKey()
    val st = remember(vm.data, key) { Calc.cycleStats(vm.data.records, vm.data.history, key) }
    val r = Dates.cycleRange(key)
    val pri = primary()
    val pop = remember { Animatable(1f) }
    LaunchedEffect(vm.switchTick) {
        if (vm.switchTick > 0) {
            pop.snapTo(0.5f)
            pop.animateTo(1f, spring(dampingRatio = 0.4f, stiffness = Spring.StiffnessMedium))
        }
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Box(Modifier.fillMaxWidth()) {
            AsyncImage(model = vm.data.theme.bg, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.matchParentSize())
            Box(Modifier.matchParentSize().background(Color.Black.copy(alpha = 0.48f)))
            Column(Modifier.statusBarsPadding().padding(horizontal = 20.dp).padding(top = 20.dp, bottom = 128.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("UCT salary", color = White, fontSize = 16.sp, fontWeight = FontWeight.Medium, modifier = Modifier.weight(1f))
                    Avatar(vm.currentUser, 28.dp, Modifier.graphicsLayer { scaleX = pop.value; scaleY = pop.value }
                        .border(1.dp, White.copy(alpha = 0.8f), CircleShape).clickable { vm.userSwitchOpen = true })
                    Spacer(Modifier.width(20.dp))
                    Icon(AppIcons.Settings, "设置", tint = White, modifier = Modifier.size(20.dp).clickable { vm.openSettingsPage(Route.Settings) })
                }
                Spacer(Modifier.height(40.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("${Dates.p2(r.startM)}.16 - ${Dates.p2(r.endM)}.15收入", color = White.copy(alpha = 0.9f), fontSize = 14.sp)
                    Spacer(Modifier.width(8.dp))
                    EyeButton(vm.homeEye, { vm.homeEye = !vm.homeEye }, tint = White.copy(alpha = 0.9f), size = 20.dp)
                }
                Spacer(Modifier.height(8.dp))
                Text(if (vm.homeEye) Fmt.money(st.net) else "****.**", color = White, fontSize = 48.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(12.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("加班时长 ${if (vm.homeEye) Fmt.hour(st.otHours) else "****"}", color = White.copy(alpha = 0.95f), fontSize = 14.sp)
                    Text("加班收入 ${if (vm.homeEye) Fmt.money(st.otIncome) else "****.**"}", color = White.copy(alpha = 0.95f), fontSize = 14.sp)
                }
            }
        }
        Column(Modifier.padding(horizontal = 16.dp).offset(y = (-96).dp).fillMaxWidth()
            .clip(RoundedCornerShape(12.dp)).background(White).padding(20.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                HomeEntry(AppIcons.Calendar, "日历", Modifier.weight(1f)) { vm.openCalendar() }
                HomeEntry(AppIcons.BarChart, "统计", Modifier.weight(1f)) { vm.openStats(0) }
                HomeEntry(AppIcons.Sign, "签到", Modifier.weight(1f)) { /* 原版此项仅展示 */ }
            }
            Spacer(Modifier.height(20.dp))
            Box(Modifier.fillMaxWidth().height(48.dp).clip(RoundedCornerShape(8.dp)).background(pri).clickable { vm.openNewRecordToday() }, contentAlignment = Alignment.Center) {
                Text("记加班", color = onPrimary(), fontSize = 16.sp, fontWeight = FontWeight.Medium)
            }
            Spacer(Modifier.height(16.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Row(Modifier.weight(1f).horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    when {
                        !vm.data.quick.show -> Text("快捷记录展示已关闭", fontSize = 12.sp, color = Gray400)
                        vm.data.quick.records.isEmpty() -> Text("暂无快捷记录", fontSize = 12.sp, color = Gray400)
                        else -> vm.data.quick.records.forEach { q -> QuickTag(q) { vm.quickRecord(q) } }
                    }
                }
                Spacer(Modifier.width(8.dp))
                Row(Modifier.clip(RoundedCornerShape(6.dp)).dashedBorder(Gray400).clickable { vm.push(Route.QuickSettings) }.padding(horizontal = 8.dp, vertical = 5.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(AppIcons.Bolt, null, tint = Gray600, modifier = Modifier.size(14.dp))
                    Spacer(Modifier.width(2.dp))
                    Text("设置", fontSize = 12.sp, color = Gray600)
                }
            }
        }
        Spacer(Modifier.height(404.dp))
    }
}'''
)
replace_region(
    'app/src/main/java/com/uct/salary/ui/screens/HomeScreen.kt',
    '@Composable\nprivate fun HomeEntry',
    '\n@Composable\nprivate fun QuickTag',
    '''@Composable
private fun HomeEntry(icon: androidx.compose.ui.graphics.vector.ImageVector, label: String, modifier: Modifier = Modifier, onClick: () -> Unit) {
    Column(modifier.clip(RoundedCornerShape(8.dp)).clickable(onClick = onClick).padding(vertical = 2.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(48.dp), contentAlignment = Alignment.Center) { Icon(icon, null, tint = Gray700, modifier = Modifier.size(28.dp)) }
        Spacer(Modifier.height(4.dp))
        Text(label, fontSize = 14.sp, color = Gray700)
    }
}'''
)
replace_once('app/src/main/java/com/uct/salary/ui/screens/HomeScreen.kt', 'import androidx.compose.ui.graphics.Brush\n', '')
replace_once('app/src/main/java/com/uct/salary/ui/screens/HomeScreen.kt', 'import com.uct.salary.ui.theme.Gray600\n', 'import com.uct.salary.ui.theme.Gray600\nimport com.uct.salary.ui.theme.Gray700\n')


replace_once(
    'app/src/main/java/com/uct/salary/ui/AppViewModel.kt',
    'import com.uct.salary.model.QuickRecord\n',
    'import com.uct.salary.model.QuickRecord\nimport com.uct.salary.model.Rates\n'
)
replace_once(
    'app/src/main/java/com/uct/salary/ui/AppViewModel.kt',
    '    fun saveDeduction(cfg: DeductionCfg) = mutateVersion(cfgKey) { it.copy(deduction = cfg) }',
    """    fun saveDeduction(cfg: DeductionCfg) {
        val list = Calc.upsertVersion(data.history, cfgKey) { it.copy(deduction = cfg) }
        val currentRates = cfg.rates ?: Calc.ratesAt(data.history, cfgKey)
        val synced = list.map { it.copy(deduction = it.deduction.copy(rates = currentRates)) }
        data = data.copy(history = synced)
        repo.saveHistory(currentUserId, synced)
    }"""
)
replace_once(
    'app/src/main/java/com/uct/salary/ui/screens/SettingsScreens.kt',
    'Text("正值输入，计算时自动取负；收支汇总的“应纳税所得额”取此值", fontSize = 11.sp, color = Gray400, modifier = Modifier.padding(top = 6.dp))',
    'Text("正值输入，计算时自动取负", fontSize = 11.sp, color = Gray400, modifier = Modifier.padding(top = 6.dp))'
)
replace_once(
    'app/src/main/java/com/uct/salary/ui/screens/CalendarScreen.kt',
    'if (isRest) "休" else Fmt.money(pay.total), fontSize = 10.sp, fontWeight = FontWeight.Medium, color = amountColor,',
    'if (isRest) "休" else Fmt.money(pay.total), fontSize = 12.sp, fontWeight = FontWeight.Bold, color = amountColor,'
)

replace_once('app/src/main/java/com/uct/salary/ui/components/Charts.kt', 'import androidx.compose.ui.graphics.drawscope.Stroke\n', 'import androidx.compose.ui.graphics.drawscope.Stroke\nimport androidx.compose.ui.graphics.nativeCanvas\nimport androidx.compose.ui.graphics.toArgb\n')
replace_once('app/src/main/java/com/uct/salary/ui/components/Charts.kt', 'import kotlin.math.abs\n', 'import android.graphics.Paint\nimport android.graphics.Typeface\nimport kotlin.math.abs\nimport kotlin.math.cos\nimport kotlin.math.sin\n')
replace_region(
    'app/src/main/java/com/uct/salary/ui/components/Charts.kt',
    '@Composable\nfun DonutChart(',
    '\n/** 竖向柱状图',
    '''@Composable
fun DonutChart(
    items: List<DonutItem>,
    centerTop: String,
    centerBottom: String,
    modifier: Modifier = Modifier,
    diameter: Dp = 190.dp
) {
    val total = items.sumOf { max(0.0, it.value) }
    val prog = remember { Animatable(0f) }
    LaunchedEffect(items) {
        prog.snapTo(0f)
        prog.animateTo(1f, tween(650, easing = FastOutSlowInEasing))
    }
    Box(modifier.fillMaxWidth().height(270.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.fillMaxWidth().height(270.dp)) {
            val stroke = 28.dp.toPx()
            val radius = min(min(size.width * 0.21f, size.height * 0.275f), diameter.toPx() / 2f)
            val cx = size.width / 2f
            val cy = size.height / 2f
            val arcTopLeft = Offset(cx - radius, cy - radius)
            val arcSize = Size(radius * 2f, radius * 2f)
            if (total <= 0.0) {
                drawArc(Gray200, 0f, 360f, false, arcTopLeft, arcSize, style = Stroke(stroke))
            } else {
                var start = -90f
                val gap = if (items.count { it.value > 0 } > 1) 2f else 0f
                val labels = ArrayList<Triple<Int, Float, Float>>()
                items.forEachIndexed { index, item ->
                    if (item.value > 0) {
                        val sweepFull = (item.value / total * 360.0).toFloat()
                        drawArc(item.color, start + gap / 2f, max(0f, (sweepFull - gap) * prog.value), false, arcTopLeft, arcSize, style = Stroke(stroke, cap = StrokeCap.Butt))
                        val middle = Math.toRadians((start + sweepFull / 2f).toDouble())
                        labels.add(Triple(index, cy + sin(middle).toFloat() * (radius + 28.dp.toPx()), cos(middle).toFloat()))
                        start += sweepFull
                    }
                }
                val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeWidth = 1.2.dp.toPx() }
                val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    textSize = 11.sp.toPx()
                    typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
                }
                val minGap = 22.dp.toPx()
                val topLimit = 14.dp.toPx()
                val bottomLimit = size.height - topLimit
                for (rightSide in listOf(false, true)) {
                    val side = labels.filter { (it.third >= 0f) == rightSide }.sortedBy { it.second }
                    val ys = side.map { it.second.coerceIn(topLimit, bottomLimit) }.toMutableList()
                    for (i in 1 until ys.size) if (ys[i] - ys[i - 1] < minGap) ys[i] = ys[i - 1] + minGap
                    if (ys.isNotEmpty() && ys.last() > bottomLimit) {
                        ys[ys.lastIndex] = bottomLimit
                        for (i in ys.lastIndex - 1 downTo 0) if (ys[i + 1] - ys[i] < minGap) ys[i] = ys[i + 1] - minGap
                    }
                    side.forEachIndexed { i, entry ->
                        val item = items[entry.first]
                        val before = items.take(entry.first).filter { it.value > 0 }.sumOf { it.value }
                        val midAngle = Math.toRadians(-90.0 + before / total * 360.0 + item.value / total * 180.0)
                        val sx = cx + cos(midAngle).toFloat() * (radius + stroke / 2f)
                        val sy = cy + sin(midAngle).toFloat() * (radius + stroke / 2f)
                        val mx = cx + cos(midAngle).toFloat() * (radius + 18.dp.toPx())
                        val my = ys[i]
                        val label = "${item.label}  ${item.valueText}"
                        val textWidth = textPaint.measureText(label)
                        val ex = if (rightSide) size.width - textWidth - 10.dp.toPx() else textWidth + 10.dp.toPx()
                        linePaint.color = item.color.toArgb()
                        drawContext.canvas.nativeCanvas.drawLine(sx, sy, mx, my, linePaint)
                        drawContext.canvas.nativeCanvas.drawLine(mx, my, ex, my, linePaint)
                        textPaint.color = item.color.toArgb()
                        textPaint.textAlign = if (rightSide) Paint.Align.LEFT else Paint.Align.RIGHT
                        val tx = if (rightSide) ex + 4.dp.toPx() else ex - 4.dp.toPx()
                        drawContext.canvas.nativeCanvas.drawText(label, tx, my + textPaint.textSize * 0.35f, textPaint)
                    }
                }
            }
        }
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(centerTop, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Gray900)
            Text(centerBottom, fontSize = 12.sp, color = Gray500)
        }
    }
}'''
)

replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals(102.16, sm.taxable, 1e-6)', 'assertEquals(200.9080459770113, sm.taxable, 1e-6)')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals(200.0, sm.taxable, 1e-6)', 'assertEquals(981.4942528735631, sm.taxable, 1e-6)')


replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals("792.33", Fmt.fixed2(c.social))', 'assertEquals("981.00", Fmt.fixed2(c.social))')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals("1028.99", Fmt.money(st.totalDeduct))', 'assertEquals("1217.66", Fmt.money(st.totalDeduct))')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals("5287.42", Fmt.money(st.net))', 'assertEquals("5098.75", Fmt.money(st.net))')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals(792.33, sm.social, 1e-6)', 'assertEquals(981.0, sm.social, 1e-6)')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals("926.83", Calc.sheetValue(SheetItem("social", ""), st))', 'assertEquals("1115.5", Calc.sheetValue(SheetItem("social", ""), st))')
replace_once('app/src/test/java/com/uct/salary/CalcTest.kt', 'assertEquals("5287.42", Calc.sheetValue(SheetItem("net", ""), st))', 'assertEquals("5098.75", Calc.sheetValue(SheetItem("net", ""), st))')

p = root / 'docs/golden_cases.json'
data = json.loads(p.read_text(encoding='utf-8'))
data['cycles']['202610']['summary']['taxable'] = 200.9080459770113
data['cycles']['202610']['summary']['social'] = 981.0
data['hs']['202610']['social'] = 981.0
data['cycles']['202610']['deductTotal'] = '-1217.66'
data['cycles']['202610']['footDeduct'] = '-1217.66'
data['cycles']['202610']['net'] = '5098.75'
data['cycles']['202610']['sheet']['social'] = '1115.5'
data['cycles']['202610']['sheet']['net'] = '5098.75'
data['cycles']['202610']['calSummary'] = data['cycles']['202610']['calSummary'].replace('应纳税所得额 102.16', '应纳税所得额 200.91').replace('合计 5421.92', '合计 5134.5').replace('个人五险 792.33', '个人五险 981')
data['cycles']['202611']['summary']['taxable'] = 981.4942528735631
data['cycles']['202611']['calSummary'] = data['cycles']['202611']['calSummary'].replace('应纳税所得额 200', '应纳税所得额 981.49').replace('合计 5661.49', '合计 4880')
p.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('PATCHED docs/golden_cases.json')
print('All HTML parity patches applied.')
