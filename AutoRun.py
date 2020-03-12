from classes.Distributor_ARN import ARN
from classes.Distributor_CPD import CPD
from classes.Combined_OW_CPD import Combined
from classes import Database_Ideal


try:
    print('CPD - Tracking')
    cpd = CPD('', '')
    cpd.shipping_from_api()
except:
    pass
try:
    print('Ariens')
    arn = ARN('ARN', 'Ariens')
    arn.inventory_from_default_to_solid()
except:
    pass
try:
    print('Hydro-Gear')
    cpd_hyd = Combined('HYD', 'Hydro-Gear')
    cpd_hyd.inventory_from_default_to_solid()
except:
    print('HYD Error')
try:
    print('AYP')
    cpd_ayp = Combined('AYP', 'AYP')
    cpd_ayp.inventory_from_default_to_solid()
except:
    print('AYP Error')
try:
    print('Champion')
    cpd_cha = Combined('CHA', 'Champion')
    cpd_cha.inventory_from_default_to_solid()
except:
    print('Champion Error')
try:
    print('Case')
    cpd_ic = Combined('IC', 'Case')
    cpd_ic.inventory_from_default_to_solid()
except:
    print('Case Error')
try:
    print('Martin-Wheel')
    cpd_mart = Combined('MART', 'Martin-Wheel')
    cpd_mart.inventory_from_default_to_solid()
except:
    print('Martin-Wheel Error')
try:
    print('MTD')
    cpd_mtd = Combined('MTD.', 'MTD')
    cpd_mtd.inventory_from_default_to_solid()
except:
    print('MTD Error')
try:
    print('NGK')
    cpd_ngk = Combined('NGK', 'NGK')
    cpd_ngk.inventory_from_default_to_solid()
except:
    print('NGK Error')
try:
    print('CPD - Kohler')
    cpd_koh = CPD('KOH', 'Kohler')
    cpd_koh.inventory_from_default_to_solid()
except:
    pass
try:
    print('CPD - Tecumseh')
    cpd_tec = CPD('TEC', 'Tecumseh')
    cpd_tec.inventory_from_default_to_solid()
except:
    pass
