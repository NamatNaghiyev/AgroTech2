#!/usr/bin/env python3
"""
AI Fermer Köməkçisi — Qayda-əsaslı chatbot modulu
Gələcəkdə LLM API inteqrasiyası üçün generate_ai_response() funksiyasını dəyişmək kifayətdir.
"""

import re
from datetime import datetime
import random

# ─── Bitki Profilləri ───
PLANT_PROFILES = {
    'pomidor': {
        'name': 'Pomidor', 'temp_min': 18, 'temp_max': 30,
        'hum_min': 60, 'hum_max': 80,
        'info': 'Gecə temperaturu 15°C-dən aşağı düşməməlidir. Yüksək rütubət fitoftora riskini artırır.'
    },
    'xiyar': {
        'name': 'Xiyar', 'temp_min': 20, 'temp_max': 32,
        'hum_min': 70, 'hum_max': 90,
        'info': 'Rütubətə həssasdır, soyuq su ilə suvarmaqdan çəkinin.'
    },
    'alma': {
        'name': 'Alma', 'temp_min': 15, 'temp_max': 25,
        'hum_min': 50, 'hum_max': 70,
        'info': 'Çiçəklənmə dövründə şaxtaya həssasdır.'
    },
    'nar': {
        'name': 'Nar', 'temp_min': 15, 'temp_max': 35,
        'hum_min': 40, 'hum_max': 60,
        'info': 'Quraqlığa nisbətən davamlıdır, lakin meyvə dövründə suvarma lazımdır.'
    },
    'taxıl': {
        'name': 'Taxıl', 'temp_min': 10, 'temp_max': 25,
        'hum_min': 50, 'hum_max': 70,
        'info': 'Cücərmə dövründə torpaq nəmliyi vacibdir.'
    },
    'pambıq': {
        'name': 'Pambıq', 'temp_min': 20, 'temp_max': 35,
        'hum_min': 50, 'hum_max': 65,
        'info': 'İsti və quru iqlimi sevir, həddindən artıq rütubət zərərlidir.'
    },
    'heyva': {
        'name': 'Heyva', 'temp_min': 15, 'temp_max': 30,
        'hum_min': 50, 'hum_max': 70,
        'info': 'Soyuğa nisbətən davamlıdır, lakin çiçəklənmə zamanı şaxta təhlükəlidir.'
    },
}

# ─── Əsas sensor kanal ID-ləri ───
KEY_CHANNELS = {
    'outside_temp': '0',
    'greenhouse_temp': ['10', '11', '12', '13'],
    'humidity': ['14', '15', '16', '17'],
    'co2': '292',
    'wind_speed': '1',
    'radiation': '4',
    'rain': '7',
    'vent_opening': ['26', '27'],
    'water_temp': ['150', '151'],
    'ec': '366',
    'ph': '368',
    'flow': '370',
    'boiler_temp': '333',
    'curtain': ['282', '283'],
}


def _get_last_daily(channel_data, n=7):
    """Kanalın son N gündəlik dəyərini qaytarır."""
    daily = channel_data.get('daily', {})
    if not daily:
        return []
    keys = sorted(daily.keys())
    last_keys = keys[-n:]
    return [(k, daily[k]) for k in last_keys]


def _avg(values):
    """Sadə ortalama."""
    if not values:
        return 0
    return sum(values) / len(values)


def calculate_trend(daily_data, days=7):
    """Son N günün trendini hesablayır: 'artır', 'azalır', 'stabil'."""
    daily = daily_data.get('daily', {})
    if not daily:
        return 'məlumat yoxdur'
    keys = sorted(daily.keys())[-days:]
    if len(keys) < 3:
        return 'kifayət qədər məlumat yoxdur'
    vals = [daily[k] for k in keys]
    first_half = _avg(vals[:len(vals)//2])
    second_half = _avg(vals[len(vals)//2:])
    diff = second_half - first_half
    if abs(diff) < 0.5:
        return 'stabil'
    return 'artır' if diff > 0 else 'azalır'


def analyze_sensors(sensor_data):
    """Bütün əsas sensorların xülasəsini çıxarır."""
    summary = {}

    # Xarici temperatur
    ch = sensor_data.get('0')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['outside_temp'] = {
            'name': 'Xarici temperatur',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'last_date': last[-1][0] if last else ch['date_to'],
            'avg': ch['avg_val'], 'min': ch['min_val'], 'max': ch['max_val'],
            'trend': calculate_trend(ch), 'unit': '°C',
        }

    # İstixana temperaturu (ortalama 4 bölmə)
    grh_vals = []
    grh_last = []
    for cid in ['10', '11', '12', '13']:
        ch = sensor_data.get(cid)
        if ch:
            grh_vals.append(ch['avg_val'])
            last = _get_last_daily(ch, 7)
            if last:
                grh_last.append(last[-1][1])
    if grh_vals:
        ref_ch = sensor_data.get('10', {})
        summary['greenhouse_temp'] = {
            'name': 'İstixana temperaturu',
            'last_val': _avg(grh_last) if grh_last else _avg(grh_vals),
            'last_date': _get_last_daily(ref_ch, 1)[-1][0] if _get_last_daily(ref_ch, 1) else '',
            'avg': _avg(grh_vals), 'min': min(sensor_data.get(c, {}).get('min_val', 0) for c in ['10','11','12','13'] if c in sensor_data),
            'max': max(sensor_data.get(c, {}).get('max_val', 0) for c in ['10','11','12','13'] if c in sensor_data),
            'trend': calculate_trend(ref_ch), 'unit': '°C',
        }

    # Rütubət (ortalama 4 bölmə)
    hum_vals = []
    hum_last = []
    for cid in ['14', '15', '16', '17']:
        ch = sensor_data.get(cid)
        if ch:
            hum_vals.append(ch['avg_val'])
            last = _get_last_daily(ch, 7)
            if last:
                hum_last.append(last[-1][1])
    if hum_vals:
        ref_ch = sensor_data.get('14', {})
        summary['humidity'] = {
            'name': 'Rütubət',
            'last_val': _avg(hum_last) if hum_last else _avg(hum_vals),
            'last_date': _get_last_daily(ref_ch, 1)[-1][0] if _get_last_daily(ref_ch, 1) else '',
            'avg': _avg(hum_vals), 'trend': calculate_trend(ref_ch), 'unit': '%',
        }

    # CO2
    ch = sensor_data.get('292')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['co2'] = {
            'name': 'CO₂ konsentrasiyası',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'last_date': last[-1][0] if last else ch['date_to'],
            'avg': ch['avg_val'], 'trend': calculate_trend(ch), 'unit': 'ppm',
        }

    # Külək
    ch = sensor_data.get('1')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['wind'] = {
            'name': 'Külək sürəti',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'unit': 'm/s',
        }

    # Radiasiya
    ch = sensor_data.get('4')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['radiation'] = {
            'name': 'Günəş radiasiyası',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'unit': 'W/m²',
        }

    # Yağış
    ch = sensor_data.get('7')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['rain'] = {
            'name': 'Yağış',
            'last_val': last[-1][1] if last else 0,
            'raining': (last[-1][1] if last else 0) > 0.5,
        }

    # EC
    ch = sensor_data.get('366')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['ec'] = {
            'name': 'EC (keçiricilik)',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'unit': 'mS/cm',
        }

    # pH
    ch = sensor_data.get('368')
    if ch:
        last = _get_last_daily(ch, 7)
        summary['ph'] = {
            'name': 'pH',
            'last_val': last[-1][1] if last else ch['avg_val'],
            'unit': 'pH',
        }

    # Ventilyasiya
    vent_last = []
    for cid in ['26', '27']:
        ch = sensor_data.get(cid)
        if ch:
            last = _get_last_daily(ch, 7)
            if last:
                vent_last.append(last[-1][1])
    if vent_last:
        summary['ventilation'] = {
            'name': 'Ventilyasiya açılması',
            'last_val': _avg(vent_last), 'unit': '%',
        }

    return summary


def check_risks(summary):
    """Sensor xülasəsinə əsasən riskləri qaytarır."""
    risks = []

    gt = summary.get('greenhouse_temp', {})
    if gt:
        t = gt.get('last_val', 0)
        if t > 35:
            risks.append('⚠️ İstixana temperaturu çox yüksəkdir ({:.1f}°C). Bitkidə istilik stressi yarana bilər. Ventilyasiyanı açın və pərdə sistemini aktivləşdirin.'.format(t))
        elif t > 30:
            risks.append('🔶 İstixana temperaturu yuxarı həddədir ({:.1f}°C). Havalandırmanı artırmağı düşünün.'.format(t))
        elif t < 5:
            risks.append('🥶 İstixana temperaturu çox aşağıdır ({:.1f}°C)! Şaxta riski var. Isıtma sistemini təcili yoxlayın.'.format(t))
        elif t < 10:
            risks.append('❄️ İstixana temperaturu aşağıdır ({:.1f}°C). Soyuğa həssas bitkilər üçün isıtmanı artırın.'.format(t))

    ot = summary.get('outside_temp', {})
    if ot and ot.get('last_val', 10) < 0:
        risks.append('🌡️ Xarici temperatur sıfırın altındadır ({:.1f}°C). Don riski var, istixana qapılarını bağlı saxlayın.'.format(ot['last_val']))

    hum = summary.get('humidity', {})
    if hum:
        h = hum.get('last_val', 50)
        if h > 85:
            risks.append('🍄 Rütubət çox yüksəkdir ({:.1f}%). Göbələk və xəstəlik riski artır. Ventilyasiyanı artırın.'.format(h))
        elif h < 40:
            risks.append('💧 Rütubət çox aşağıdır ({:.1f}%). Bitkidə su stressi yarana bilər.'.format(h))

    co2 = summary.get('co2', {})
    if co2:
        c = co2.get('last_val', 400)
        if c > 1200:
            risks.append('🌿 CO₂ səviyyəsi çox yüksəkdir ({:.0f} ppm). Ventilyasiya lazımdır.'.format(c))
        elif c < 200:
            risks.append('🌿 CO₂ səviyyəsi çox aşağıdır ({:.0f} ppm). Fotosintez yavaşlaya bilər, CO₂ dozajını artırın.'.format(c))

    ph = summary.get('ph', {})
    if ph:
        p = ph.get('last_val', 7)
        if p > 7.5:
            risks.append('⚗️ pH çox yüksəkdir ({:.1f}). Su keyfiyyətini yoxlayın.'.format(p))
        elif p < 5.5:
            risks.append('⚗️ pH çox aşağıdır ({:.1f}). Su turşuluğu problemi ola bilər.'.format(p))

    ec = summary.get('ec', {})
    if ec:
        e = ec.get('last_val', 1)
        if e > 3.0:
            risks.append('⚡ EC çox yüksəkdir ({:.1f} mS/cm). Duz konsentrasiyası bitkiyə zərər verə bilər.'.format(e))

    return risks


def detect_intent(message):
    """Fermerin mesajından niyyəti müəyyən edir."""
    msg = message.lower().strip()

    smalltalk_patterns = {
        'greeting': ['salam', 'sabahın xeyir', 'axşamın xeyir', 'xoş gördük'],
        'farewell': ['sağ ol', 'xudahafiz', 'hələlik'],
        'thanks': ['təşəkkür', 'çox sağ ol', 'minnətdaram', 'əla', 'təşəkkürlər'],
        'smalltalk': ['necəsən', 'nə var', 'necə gedir', 'kefin necədir'],
        'identity': ['adın nədir', 'kimsən', 'sən kimsən', 'özünü təqdim et'],
        'motivation': ['motivasiya', 'yorulmuşam', 'həvəsim yoxdur', 'məsləhət ver', 'çətin']
    }

    smalltalk_intents = []
    for st_intent, keywords in smalltalk_patterns.items():
        if any(kw in msg for kw in keywords):
            smalltalk_intents.append(st_intent)

    agro_intent = None
    agro_extra = None

    for plant in PLANT_PROFILES:
        if plant in msg:
            agro_extra = plant
            break

    patterns = [
        ('suvarma', ['suvar', 'su ver', 'su laz', 'nəmlə', 'quru', 'nəmlik', 'torpaq']),
        ('temperatur', ['temperatur', 'dərəcə', 'isti', 'soyuq', 'şaxta', 'don', 'istilik']),
        ('rütubət', ['rütubət', 'nəm', 'humid', 'rütubətli']),
        ('risk', ['risk', 'təhlükə', 'xəstəlik', 'göbələk', 'problem', 'xəbərdarlıq']),
        ('co2', ['co2', 'karbon', 'hava keyfiyyəti']),
        ('sukeyfiyyeti', ['ec', 'ph', 'su keyfiyyət', 'turşu', 'duz']),
        ('hava', ['hava', 'külək', 'yağış', 'günəş', 'radiasiya']),
        ('trend', ['trend', 'artır', 'azalır', 'artım', 'düşür', 'qrafik', 'son günlərdə']),
        ('general', ['vəziyyət', 'normaldır', 'yaxşıdır', 'göstərici', 'analiz'])
    ]

    for intent, keywords in patterns:
        for kw in keywords:
            if len(kw) <= 2:
                if re.search(r'\b' + re.escape(kw) + r'\b', msg):
                    agro_intent = intent
                    break
            else:
                if kw in msg:
                    agro_intent = intent
                    break
        if agro_intent:
            break

    if agro_extra and not agro_intent:
        agro_intent = 'plant'

    return agro_intent, agro_extra, smalltalk_intents


def handle_smalltalk(smalltalk_intents, has_agro=False):
    """Gündəlik danışıq üçün səmimi cavablar hazırlayır."""
    responses = []
    
    if 'greeting' in smalltalk_intents:
        greetings = [
            "Salam!", 
            "Xoş gördük!", 
            "Salam! AgroTech köməkçisi xidmətinizdədir."
        ]
        responses.append(random.choice(greetings))
        
    if 'identity' in smalltalk_intents:
        responses.append("Mən AgroTech AI Fermer Köməkçisiyəm. İstixana və sahənizdəki sensor məlumatlarını analiz edib sizə ən uyğun aqro məsləhətləri vermək üçün buradayam.")
        
    if 'smalltalk' in smalltalk_intents:
        responses.append("Yaxşıyam, təşəkkür edirəm! Ümid edirəm sahədə işlər qaydasındadır. Mən sahədəki göstəriciləri izləməyə və fermerə düzgün qərar verməkdə kömək etməyə hazıram.")
        
    if 'motivation' in smalltalk_intents:
        responses.append("Əkinçilik asan iş deyil, amma əziyyətinizin bəhrəsini mütləq görəcəksiniz. Bir az dincəlin, texniki işləri və analizləri mənə etibar edə bilərsiniz!")
        
    if 'thanks' in smalltalk_intents:
        responses.append("Buyurun, hər zaman kömək etməyə hazıram. Dəyişiklik olsa, yenə soruşa bilərsiniz.")
        
    if 'farewell' in smalltalk_intents:
        responses.append("Sağ olun! Uğurlu və bol məhsullu gün arzulayıram.")
        
    # Əgər aqro sual yoxdursa və smalltalk varsa, yönləndirmə əlavə edək
    if not has_agro:
        if 'greeting' in smalltalk_intents and len(smalltalk_intents) == 1:
            responses.append("İstəsəniz, sahənin hazırkı sensor vəziyyətini analiz edə, suvarma və risklər barədə məsləhət verə bilərəm.")
            
    return " ".join(responses).strip()


def handle_sensor_question(intent, extra, summary, risks, history_plant):
    """Sensor və aqro suallar üçün analizli cavab hazırlayır."""
    parts = []
    
    if not summary:
        return "Hazırda sensor datasını oxuya bilmirəm, lakin ümumi aqro məsləhət verə bilərəm. Dəqiq qərar üçün sahəni fiziki yoxlamağınız tövsiyə olunur."
        
    if intent == 'plant':
        parts.append(_get_plant_advice(extra, summary))
    elif intent == 'suvarma':
        parts.append(_handle_irrigation_question(summary))
    elif intent == 'temperatur':
        gt = summary.get('greenhouse_temp', {})
        ot = summary.get('outside_temp', {})
        parts.append("🌡️ Temperatur Analizi:")
        if gt:
            t = gt.get('last_val', 0)
            parts.append(f"  İstixana: {t:.1f}°C — {'normal (18-30°C arası)' if 18 <= t <= 30 else 'DİQQƏT! normal aralıqdan kənardır'}")
            parts.append(f"  Trend: {gt.get('trend', '?')}")
        if ot:
            parts.append(f"  Xarici: {ot.get('last_val', 0):.1f}°C")
    elif intent == 'rütubət':
        hum = summary.get('humidity', {})
        if hum:
            h = hum.get('last_val', 0)
            parts.append(f"💧 Rütubət Analizi:")
            parts.append(f"  Dəyər: {h:.1f}%")
            parts.append(f"  Trend: {hum.get('trend', '?')}")
            if h > 85:
                parts.append("  ⚠️ Çox yüksəkdir — göbələk və xəstəlik riski var!")
            elif h < 40:
                parts.append("  ⚠️ Çox aşağıdır — bitkidə su stressi yarana bilər.")
            else:
                parts.append("  ✅ Normal aralıqdadır.")
    elif intent == 'co2':
        co2 = summary.get('co2', {})
        if co2:
            c = co2.get('last_val', 400)
            parts.append(f"🌿 CO₂ Analizi:")
            parts.append(f"  Konsentrasiya: {c:.0f} ppm")
            parts.append(f"  Trend: {co2.get('trend', '?')}")
            if 300 <= c <= 800:
                parts.append("  ✅ Normal aralıqdadır.")
            elif c > 1200:
                parts.append("  ⚠️ Çox yüksək! Ventilyasiya açın.")
    elif intent == 'sukeyfiyyeti':
        ph = summary.get('ph', {})
        ec = summary.get('ec', {})
        parts.append("⚗️ Su Keyfiyyəti:")
        if ph:
            parts.append(f"  pH: {ph.get('last_val', 0):.1f}")
        if ec:
            parts.append(f"  EC: {ec.get('last_val', 0):.2f} mS/cm")
    elif intent == 'hava':
        parts.append("🌤️ Hava Məlumatı:")
        for key in ['outside_temp', 'wind', 'radiation', 'rain']:
            s = summary.get(key)
            if s:
                parts.append(f"  {s['name']}: {s.get('last_val', 0):.1f} {s.get('unit', '')}")
    elif intent == 'trend':
        parts.append("📊 Trend Analizi (Son günlərin göstəriciləri):")
        for key in ['greenhouse_temp', 'humidity', 'co2']:
            s = summary.get(key)
            if s:
                trend = s.get('trend', 'məlumat yoxdur')
                trend_icon = {'artır': '📈', 'azalır': '📉', 'stabil': '➡️'}.get(trend, '')
                parts.append(f"  {s['name']}: {trend} {trend_icon}")
    elif intent == 'risk':
        if risks:
            parts.append("⚠️ Təhlükə və Risklər Təsbit Edildi:")
            for r in risks:
                parts.append(f"  {r}")
        else:
            parts.append("✅ Hazırda ciddi bir risk və ya təhlükə görünmür.")
    else:
        parts.append("📊 Hazırkı Vəziyyətin Xülasəsi:")
        parts.append(_format_summary_text(summary))
        parts.append("\n🔍 Ümumi Analiz:")
        gt = summary.get('greenhouse_temp', {})
        hum = summary.get('humidity', {})
        if gt:
            t = gt.get('last_val', 20)
            if 18 <= t <= 30:
                parts.append(f"  ✅ İstixana temperaturu normal ({t:.1f}°C)")
            else:
                parts.append(f"  ⚠️ İstixana temperaturu diqqət tələb edir ({t:.1f}°C)")
        if hum:
            h = hum.get('last_val', 60)
            if 40 <= h <= 85:
                parts.append(f"  ✅ Rütubət qənaətbəxşdir ({h:.1f}%)")
            else:
                parts.append(f"  ⚠️ Rütubət normal aralıqdan kənardır ({h:.1f}%)")
                
    if intent != 'risk' and risks:
        parts.append("\n⚠️ Xəbərdarlıqlar:")
        for r in risks:
            parts.append(f"  {r}")

    # Kontekst əsaslı bitki tövsiyəsi
    if extra and intent != 'plant':
        parts.append('\n' + _get_plant_advice(extra, summary))
    elif history_plant and intent != 'plant':
        parts.append('\n' + _get_plant_advice(history_plant, summary))
        
    return '\n'.join(parts)


def _format_summary_text(summary):
    """Sensor xülasəsini mətn olaraq formatlayır."""
    lines = []
    mapping = [
        ('greenhouse_temp', '🌡️ İstixana temperaturu'),
        ('outside_temp', '🌤️ Xarici temperatur'),
        ('humidity', '💧 Rütubət'),
        ('co2', '🌿 CO₂'),
        ('wind', '💨 Külək'),
        ('radiation', '☀️ Radiasiya'),
    ]
    for key, label in mapping:
        s = summary.get(key)
        if s:
            val = s.get('last_val', 0)
            unit = s.get('unit', '')
            trend = s.get('trend', '')
            trend_icon = {'artır': '📈', 'azalır': '📉', 'stabil': '➡️'}.get(trend, '')
            line = f"  {label}: {val:.1f} {unit}"
            if trend:
                line += f" ({trend} {trend_icon})"
            lines.append(line)
    return '\n'.join(lines)


def _get_plant_advice(plant_key, summary):
    """Bitkiyə uyğun tövsiyə qaytarır."""
    profile = PLANT_PROFILES.get(plant_key)
    if not profile:
        return ''

    lines = [f"\n🌱 {profile['name']} üçün analiz:"]

    gt = summary.get('greenhouse_temp', {})
    temp = gt.get('last_val', 20) if gt else 20

    hum_data = summary.get('humidity', {})
    hum = hum_data.get('last_val', 60) if hum_data else 60

    if temp < profile['temp_min']:
        lines.append(f"  🥶 Temperatur ({temp:.1f}°C) {profile['name']} üçün aşağıdır (min {profile['temp_min']}°C). İsıtmanı artırın.")
    elif temp > profile['temp_max']:
        lines.append(f"  🔥 Temperatur ({temp:.1f}°C) {profile['name']} üçün yüksəkdir (max {profile['temp_max']}°C). Havalandırma lazımdır.")
    else:
        lines.append(f"  ✅ Temperatur ({temp:.1f}°C) {profile['name']} üçün uyğundur ({profile['temp_min']}-{profile['temp_max']}°C).")

    if hum < profile['hum_min']:
        lines.append(f"  💧 Rütubət ({hum:.1f}%) {profile['name']} üçün aşağıdır (min {profile['hum_min']}%).")
    elif hum > profile['hum_max']:
        lines.append(f"  💧 Rütubət ({hum:.1f}%) {profile['name']} üçün yüksəkdir (max {profile['hum_max']}%). Xəstəlik riski arta bilər.")
    else:
        lines.append(f"  ✅ Rütubət ({hum:.1f}%) {profile['name']} üçün normaldır ({profile['hum_min']}-{profile['hum_max']}%).")

    lines.append(f"  ℹ️ {profile['info']}")
    return '\n'.join(lines)


def _handle_irrigation_question(summary):
    """Suvarma ilə bağlı cavab."""
    lines = ["💧 Suvarma Analizi:"]
    hum = summary.get('humidity', {})
    gt = summary.get('greenhouse_temp', {})
    rain = summary.get('rain', {})

    h_val = hum.get('last_val', 60) if hum else 60
    t_val = gt.get('last_val', 20) if gt else 20
    raining = rain.get('raining', False) if rain else False

    lines.append(f"\n  Rütubət: {h_val:.1f}%")
    lines.append(f"  Temperatur: {t_val:.1f}°C")

    if raining:
        lines.append("\n  🌧️ Hal-hazırda yağış var, suvarmanı dayandırmaq olar.")
    elif h_val < 40:
        lines.append("\n  Bu göstəricilərə əsasən rütubət aşağıdır. Suvarma tövsiyə olunur.")
        lines.append("  Gecə və ya səhər erkən suvarma daha effektivdir.")
    elif h_val < 55:
        lines.append("\n  Rütubət orta səviyyədədir. Torpağı əllə yoxlayın — qurudursa, yüngül suvarma edə bilərsiniz.")
    else:
        lines.append("\n  Rütubət kifayət qədərdir. Hazırda əlavə suvarmaya ehtiyac görünmür.")
        lines.append("  Həddindən artıq suvarma kök çürüməsi yarada bilər.")

    if t_val > 30:
        lines.append("  ⚠️ Temperatur yüksəkdir — buxarlanma sürətli olacaq. Suvarsanız, daha çox su lazım ola bilər.")

    lines.append("\n  ⚡ Qeyd: Bu sistemdə torpaq nəmliyi sensoru quraşdırılmayıb. Dəqiq qərar üçün sahəni də yoxlamaq lazımdır.")
    return '\n'.join(lines)


def _use_history_context(message, history):
    """Tarixçədən kontekst çıxarır (əvvəlki sualda bitki adı varsa və s.)."""
    if not history:
        return None
    for entry in reversed(history[-10:]):
        text = entry.get('text', '').lower()
        for plant in PLANT_PROFILES:
            if plant in text:
                return plant
    return None


def generate_ai_response(user_message, sensor_data, conversation_history=None):
    """
    ★ ƏSAS FUNKSIYA — Gələcəkdə LLM API buraya əlavə olunacaq.
    """
    summary = analyze_sensors(sensor_data)
    risks = check_risks(summary)
    
    agro_intent, agro_extra, smalltalk_intents = detect_intent(user_message)
    history_plant = _use_history_context(user_message, conversation_history)
    
    # Əgər aqro sualı başa düşülməyibsə və smalltalk da yoxdursa, general verək
    if not agro_intent and not smalltalk_intents:
        agro_intent = 'general'
        
    final_response_parts = []
    
    if smalltalk_intents:
        st_response = handle_smalltalk(smalltalk_intents, has_agro=bool(agro_intent))
        if st_response:
            final_response_parts.append(st_response)
            
    if agro_intent:
        if final_response_parts:
            final_response_parts.append("") # Boş sətir əlavə edirik ayırmaq üçün
            
        agro_response = handle_sensor_question(agro_intent, agro_extra, summary, risks, history_plant)
        final_response_parts.append(agro_response)
        
    return '\n'.join(final_response_parts).strip()
