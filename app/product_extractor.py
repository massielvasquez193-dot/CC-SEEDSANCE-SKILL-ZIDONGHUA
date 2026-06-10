"""
TikTok AI Video Factory - 产品分析模块 (P2)
功能: 读取产品图片，输出产品名称/颜色/包装/材质/规格/卖点，保存product.json
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ProductExtractor:
    """产品信息提取器 — 从产品图片中提取结构化产品数据"""

    # 产品品类映射
    CATEGORY_KEYWORDS = {
        "护肤品": ["精华", "面霜", "乳液", "化妆水", "面膜", "防晒", "眼霜", "洁面", "卸妆", "护肤", "skincare", "cream", "serum", "lotion"],
        "彩妆": ["口红", "唇膏", "粉底", "眼影", "腮红", "眉笔", "睫毛膏", "散粉", "气垫", "lipstick", "foundation", "makeup"],
        "食品": ["零食", "饮料", "糖果", "饼干", "巧克力", "坚果", "咖啡", "茶", "food", "snack", "drink"],
        "电子产品": ["手机", "耳机", "充电器", "数据线", "音箱", "手表", "平板", "phone", "earphone", "charger"],
        "服装": ["T恤", "衬衫", "裙子", "裤子", "外套", "卫衣", "连衣裙", "dress", "shirt", "jacket"],
        "家居用品": ["香薰", "蜡烛", "收纳", "抱枕", "地毯", "装饰", "candle", "home"],
        "个人护理": ["洗发水", "沐浴露", "身体乳", "护手霜", "牙膏", "香水", "shampoo", "perfume"],
        "母婴": ["奶粉", "尿布", "玩具", "奶瓶", "baby"],
        "保健品": ["维生素", "蛋白粉", "鱼油", "钙片", "supplement", "vitamin"],
        "宠物用品": ["狗粮", "猫粮", "宠物玩具", "pet"],
    }

    # 颜色关键词
    COLOR_KEYWORDS = {
        "红色": ["红", "red", "crimson", "#ff", "朱红", "绯红", "酒红", "ruby"],
        "粉色": ["粉", "pink", "rose", "桃红", "樱花粉", " blush"],
        "白色": ["白", "white", " ivory", "奶白", "纯白", "米白"],
        "黑色": ["黑", "black", "dark", "墨", "炭黑"],
        "蓝色": ["蓝", "blue", "navy", "天蓝", "宝蓝", "cyan"],
        "绿色": ["绿", "green", "emerald", "抹茶", "薄荷绿"],
        "金色": ["金", "gold", "rose gold", "香槟", "玫瑰金"],
        "银色": ["银", "silver", "platinum"],
        "紫色": ["紫", "purple", "violet", "lavender", "薰衣草"],
        "黄色": ["黄", "yellow", "amber", "柠檬黄", "姜黄"],
        "橙色": ["橙", "orange", "tangerine", "珊瑚橙"],
        "棕色": ["棕", "brown", "coffee", "摩卡", "巧克力色"],
        "透明": ["透明", "transparent", "clear", "glass"],
        "灰色": ["灰", "gray", "grey", "charcoal", "烟灰"],
    }

    # 包装类型
    PACKAGING_KEYWORDS = {
        "瓶装": ["瓶", "bottle", "jar", "瓶身"],
        "管装": ["管", "tube", "软管"],
        "盒装": ["盒", "box", "套装", "礼盒", "gift set"],
        "袋装": ["袋", "pack", "pouch", "sachet", "refill"],
        "罐装": ["罐", "tin", "can", "pot", "jar"],
        "喷雾": ["喷雾", "spray", "mist", "pump"],
        "滴管": ["滴管", "dropper", "pipette"],
        "按压": ["按压", "pump", "dispenser"],
        "便携装": ["便携", "travel", "mini", "小样", "sample"],
    }

    # 材质关键词
    MATERIAL_KEYWORDS = {
        "玻璃": ["玻璃", "glass"],
        "塑料": ["塑料", "plastic", "PET", "PP", "亚克力", "acrylic"],
        "金属": ["金属", "metal", "aluminum", "铝", "不锈钢", "stainless"],
        "纸质": ["纸", "paper", "cardboard", "卡纸"],
        "陶瓷": ["陶瓷", "ceramic", "porcelain"],
        "硅胶": ["硅胶", "silicone", "rubber"],
        "木质": ["木", "wood", "bamboo", "竹"],
    }

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    # ================================================================
    # 主提取方法
    # ================================================================
    def extract(self, image_path: Path) -> dict:
        """
        从产品图片提取完整产品信息
        Returns: 产品名称/品牌/品类/颜色/包装/材质/规格/卖点/目标用户/价格区间
        """
        logger.info(f"提取产品信息: {image_path.name}")

        product = {
            "file_name": image_path.name,
            "file_path": str(image_path),
            "file_size_bytes": image_path.stat().st_size if image_path.exists() else 0,
            "format": image_path.suffix.lower(),
            "product_name": "",
            "brand": "",
            "category": "",
            "sub_category": "",
            "color": "",
            "color_hex": "",
            "packaging": "",
            "packaging_detail": "",
            "material": "",
            "specifications": {},
            "key_features": [],
            "target_audience": "",
            "price_range": "",
            "usage_scenario": "",
            "extraction_method": "heuristic",
        }

        # 从文件名推断
        filename_info = self._parse_filename(image_path.stem)
        product.update(filename_info)

        # AI视觉分析 (如果可用)
        if self.ai_client:
            try:
                ai_info = self._ai_analyze(image_path)
                if ai_info:
                    product.update(ai_info)
                    product["extraction_method"] = "ai"
            except Exception as e:
                logger.error(f"AI产品分析失败: {e}")

        # 补充推断
        product = self._enrich_product(product)

        return product

    # ================================================================
    # 文件名解析
    # ================================================================
    def _parse_filename(self, filename: str) -> dict:
        """
        解析文件名提取产品信息
        支持格式:
          - brand_product-name_color
          - brand_product_name_color_packaging
          - product_name
        """
        info = {}
        # 替换分隔符
        clean = filename.replace("-", "_").replace(" ", "_")
        parts = [p for p in clean.split("_") if p]

        if len(parts) >= 3:
            info["brand"] = parts[0]
            info["product_name"] = parts[1]
            info["color"] = parts[2] if len(parts) > 2 else ""
        elif len(parts) == 2:
            info["brand"] = parts[0]
            info["product_name"] = parts[1]
        elif len(parts) == 1:
            info["product_name"] = parts[0]
            info["brand"] = ""

        # 从产品名推断品类
        if info.get("product_name"):
            info["category"] = self._infer_category(info["product_name"])

        # 从产品名推断颜色
        if info.get("product_name") and not info.get("color"):
            info["color"] = self._infer_color(info["product_name"])

        return info

    # ================================================================
    # 推断方法
    # ================================================================
    def _infer_category(self, name: str) -> str:
        """从产品名推断品类"""
        name_lower = name.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in name_lower:
                    return category
        return "其他"

    def _infer_color(self, text: str) -> str:
        """从文本推断颜色"""
        text_lower = text.lower()
        for color_name, keywords in self.COLOR_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    return color_name
        return ""

    def _infer_packaging(self, text: str) -> str:
        """推断包装类型"""
        text_lower = text.lower()
        for pkg_type, keywords in self.PACKAGING_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    return pkg_type
        return ""

    def _infer_material(self, text: str) -> str:
        """推断材质"""
        text_lower = text.lower()
        for mat, keywords in self.MATERIAL_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    return mat
        return ""

    # ================================================================
    # 产品信息丰富
    # ================================================================
    def _enrich_product(self, product: dict) -> dict:
        """基于已有信息补充推断"""
        name = product.get("product_name", "")

        # 补充品类
        if not product.get("category"):
            product["category"] = self._infer_category(name)

        # 补充包装
        if not product.get("packaging"):
            product["packaging"] = self._infer_packaging(name)

        # 补充材质
        if not product.get("material"):
            product["material"] = self._infer_material(name)

        # 补充卖点
        if not product.get("key_features"):
            product["key_features"] = self._generate_features(product)

        # 补充目标用户
        if not product.get("target_audience"):
            product["target_audience"] = self._infer_target_audience(product)

        # 补充规格
        if not product.get("specifications"):
            product["specifications"] = self._infer_specifications(product)

        return product

    def _generate_features(self, product: dict) -> list[str]:
        """生成产品卖点"""
        features = []
        category = product.get("category", "")
        color = product.get("color", "")
        material = product.get("material", "")
        packaging = product.get("packaging", "")

        category_features = {
            "护肤品": ["保湿补水", "温和不刺激", "快速吸收", "持久滋润"],
            "彩妆": ["显色度高", "持久不脱妆", "轻薄服帖", "自然妆感"],
            "食品": ["口感绝佳", "真材实料", "健康无添加", "便携包装"],
            "电子产品": ["高性价比", "品质保证", "便携设计", "续航持久"],
            "服装": ["面料舒适", "版型显瘦", "百搭款式", "做工精细"],
            "家居用品": ["高颜值", "实用性强", "提升幸福感", "送礼佳品"],
            "个人护理": ["温和配方", "持久留香", "深层清洁", "专业护理"],
        }

        features = category_features.get(category, ["高品质", "性价比高", "值得信赖"])

        if material:
            features.insert(0, f"{material}材质")
        if color:
            features.insert(0, f"{color}外观")

        return features[:5]

    def _infer_target_audience(self, product: dict) -> str:
        """推断目标用户"""
        category_audience = {
            "护肤品": "18-40岁注重护肤的女性",
            "彩妆": "18-35岁爱美的年轻女性",
            "食品": "全年龄段消费者",
            "电子产品": "18-45岁科技爱好者",
            "服装": "18-35岁追求时尚的年轻人",
            "个人护理": "20-45岁注重生活品质的人群",
            "母婴": "25-40岁的新手父母",
            "保健品": "25-55岁关注健康的人群",
        }
        return category_audience.get(product.get("category", ""), "泛消费人群")

    def _infer_specifications(self, product: dict) -> dict:
        """推断产品规格"""
        specs = {}
        category = product.get("category", "")
        if category == "护肤品":
            specs = {"容量": "30-50ml", "保质期": "3年", "适用肤质": "所有肤质"}
        elif category == "食品":
            specs = {"净含量": "100-500g", "保质期": "6-12个月", "储存方式": "阴凉干燥"}
        elif category == "电子产品":
            specs = {"重量": "轻便", "接口": "Type-C", "兼容": "多平台"}
        return specs

    # ================================================================
    # AI分析
    # ================================================================
    def _ai_analyze(self, image_path: Path) -> dict:
        """使用AI视觉分析产品图片"""
        if not self.ai_client:
            return {}

        try:
            prompt = """分析这个产品图片，提取以下结构化信息，严格以JSON格式返回：
{
    "product_name": "产品具体名称",
    "brand": "品牌名",
    "category": "产品大类(护肤品/彩妆/食品/电子产品/服装/家居用品/个人护理/母婴/保健品/宠物用品)",
    "sub_category": "产品子类",
    "color": "产品主色调描述(红/白/黑/金/粉/蓝/绿/紫...)",
    "color_hex": "近似颜色hex值",
    "packaging": "包装类型(瓶装/管装/盒装/袋装/罐装/喷雾/滴管/按压/便携装)",
    "packaging_detail": "包装具体描述",
    "material": "材质(玻璃/塑料/金属/纸质/陶瓷/硅胶/木质)",
    "specifications": {"容量": "", "尺寸": "", "重量": ""},
    "key_features": ["核心卖点1", "核心卖点2", "核心卖点3"],
    "target_audience": "目标用户群体",
    "price_range": "价格定位(平价/中端/高端/奢侈)",
    "usage_scenario": "使用场景描述"
}"""
            # 实际调用AI视觉API
            # response = self.ai_client.analyze_image(image_path, prompt)
            # return json.loads(response)
            return {}
        except Exception:
            return {}

    # ================================================================
    # 一致性描述 & 保存
    # ================================================================
    def generate_consistency_description(self, product: dict) -> str:
        """生成产品一致性描述，用于所有镜头Prompt"""
        return (
            f"产品一致性: {product.get('brand', '')} {product.get('product_name', '')}, "
            f"{product.get('color', '')}色, "
            f"{product.get('packaging', '')}包装, "
            f"{product.get('material', '')}材质, "
            f"品类: {product.get('category', '')}。"
            f"所有镜头必须保持同一产品、同一包装、同一颜色、同一品牌、同一尺寸、同一材质。"
            f"禁止改变产品外观、禁止替换品牌元素、禁止改变包装设计。"
        )

    def save_product_json(self, product: dict, output_dir: Path) -> Path:
        """保存 product.json"""
        output_dir.mkdir(parents=True, exist_ok=True)
        product["extracted_at"] = datetime.now().isoformat()

        json_path = output_dir / "product.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(product, f, ensure_ascii=False, indent=2)
        logger.info(f"product.json 已保存: {json_path}")
        return json_path

    def batch_extract(self, image_paths: list[Path]) -> list[dict]:
        """批量提取产品信息"""
        return [self.extract(p) for p in image_paths]
