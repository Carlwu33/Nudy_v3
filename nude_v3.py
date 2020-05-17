import sys
import os
import _io
from collections import namedtuple
from PIL import Image

class Nude:
    Skin = namedtuple("Skin", "id skin region x y")

    def __init__(self, path_or_image):
#若 Path_or_image 为 Image.Image类型的实例，直接赋值，若为str类型的实例，则打开图片
    if isinstance(path_or_image, Image.Image):
        self.image = path_or_image
    elif isinstance(path_or_image, str):
        self.image = Image.open(path_or_image)

# 获得图片所有颜色通道
    bands = self.image.getbands()
# 判断是否为单通道图片（即灰度图），是则将灰度图转为RGB图
    if len(bands) == 1:
# 新建相同大小的RGB图像
        new_img = Image.new("RGB", self.image.size)
# 拷贝灰度图到RGB图(PIL自动进行颜色通道转换）
        new_img.paste(self.image)
        f = self.image.filename
# 替换self.image
        self.image = new_img
        self.image.filename = f

# 存储对应图像所有像素的全部 Skin 对象
        self.skin_map = []
# 检测到的皮肤区域，元素的索引即为皮肤区域号，元素都是包含一些Skin对象的列表
        self.detected_region = []
# 元素区域号代表的都是待合并的区域
        self.merge_regions = []
# 整合后的皮肤区域
        self.skin_region = []
# 最近合并的两个皮肤区域的区域号，初始化都为-1
        self.last_from, self.last_to = -1, -1
# 色情图片判断结果
        self.result = None
# 处理得到的信息
        self.message = None
# 图像宽和高
        self.width, self.height = self.image.size
# 图像总像素
        self.total_pixels = self.width * self.height
    def resize(self, maxwidth=1000, maxheight=1000)

        """
        基于最大宽高比例重新设定图片的大小，
        注意：这可能影响检测算法的结果

        如果没有变化返回 0
        原宽度大于最大值， 返回1
        原高度大于maxheight,返回2
        原宽高都大于最大值，返回 3

        """
# ret 用于存储返回值
        ret = 0
        if maxwidth:
            if self.width > maxwidth:
                wpercent = (maxwidth / self.width)
                hsize = int((self.height * wpercent)
                fname = self.image.filename
# Image.LANCZOS 是重采样滤波器，用于抗锯齿
                self.image = self.image.resize((maxwidth, hsize), Image.LANCZOS)
                self.image.filename = fname
                self.width, self.height = self.image.size
                self.total_pixels = self.width * self.height
                ret +=1
        if maxheight:
            if self.height > maxheight:
                hpercent = (maxheight /  float(self.height))
                wsize = int((float(self.width) * float(hpercent)))
                fname = self.image.filename
                self.image = self.image.resize((wsize, maxheight), Image.LANCZOS)
                self.image.filename = fname
                self.width, self.height = self.image.size
                self.total_pixels = self.width * self.height
                ret += 2
        return ret
    def parse(self):
        # 如果已有结果，返回本对象
        if self.result is not None:
            return self
        # 获得图片所有像素数据
        pixels = self.image.load()

        # 遍历每个像素，为每个像素创建Skin对象，其中self._classify_skin()这个方法是检测像素颜色是否为肤色:
        for y in range(self.height):
            for x in range(self.width):
# 获取像素RGB三个通道的值, [X, Y]是[(x, y)]的简便写法
                r = pixels[x, y][0] # red
                g = pixels[x, y][1] # green
                b = pixels[x, y][2] # blue
#判断当前像素是否为肤色
                isSkin = True if self._classify_skin(r, g, b) else False
# 给每个像素分配唯一 id值（1, 2, 3 ... height * width), 注意x, y值是从零 开始的
                _id = x + y * self.width + 1
# 为每个像素创建一个对应的Skin 对象， 并添加到self.skin_map中
                self.skin_map.append(self.Skin(_id, isSkin, None, x, y))
                # 若当前像素不是肤色像色，则跳出本次循环
                if  not isSkin:
                    continue

                # 若当前像素是肤色像素，那么就要处理了，先遍历它的相邻像素

                check_indexes = [_id -2, # 当前像素左方的像素
                                _id - self.width -2, # 当前像素左上方的像素
                                _id - self.width -1, #当前像素的上方像素
                                _id - self.width] # 当前像素右上方的像素
                region = -1 # 用来记录相邻像素所在的区域号，初始化为-1

# 遍历每一个相邻像素的索引
                for index in check_indexes:
# 尝试索引相邻像素的Skin对象，没有则跳出循环
                    try:
                        self.skin_map[index]
                    except IndexError:
                        break
# 相邻像素若为肤色像素：
                    if self.skin_map[index].skin:
# 若相邻像素与当前像素的region均为有效值，且二者不同，且未添加相同的合并任务
                        if (self.skin_map[index].region != None and
                                region != None and region != -1 and
                                self.skin_map[index].region !=region and
                                self.last_from != region and
                                self.last_to != self.skin_map[index].region):
# 那么就添加这两个区域的合并任务
                        self._add_merge(region, self.skin.skin_map[index].region)
              # 记录此相邻像素所在的区域号
              region = self.skin_map[index].region
              # 遍历完所有相邻像素后
              if region == -1:
# 更改属性为新的区域号，注意元组是不可变类型，不能直接修改属性
                  _skin = self.skin_map[_id -1]._replace(region=len(self.detected_regions))
                  self.skin_map[_id -1] = _skin
# 将此肤色像素所在的区域建为新区域
                  self.detected_regions.append([self.skin_map[_id -1]])
# region 不等于 -1的同时不等于None, 说明有区域号为有效值的相邻肤色像素像素
              elif region != None:
# 将此像素的区域号更改为与相邻像素相同
                  _skin = self.skin_map[_id -1]._replace(region=region)
                  self.skin_map[_id -1] =_skin
# 向这个区域的像素列表中添加此像素
                  self.detected_regions[region].append(self.skin_map[_id -1])

# 遍历完所有的像素之后，图片的皮肤区域划分初步完成了，只是在变量self.merge_regions还有一连通的皮肤区域号，他们需要合并，合并之后就可以进行情色判定了
        self._merge(self.detected_regions, self.merge_regions)
# 分析皮肤区域，得到判定结果
        self._analyse_regions()
        return self

# 基于像素的肤色检测技术
    def _classify_skin(self, r, g, b):
#  根据RGB的值去判断
        rgb_classifier = r > 95 and \
                g > 40 and g < 100 and \
                b > 20 and \
                max([r, g, b]) -min([r, g, b]) > 15 and \
                abs(r -g) > 15 and \
                r > g and \
                r > b

# 根据处理后的RGB值判定
        nr, ng, nb = self._to_normalized(r, g ,b)
        norm_rgb_classifier = nr / ng > 1.185 and \
                float(r * b) / ((r + g + b) ** 2) > 0.107 and \
                float(r * g) / ((r + g + b) ** 2) > 0.112

# HSV 颜色模式下的判定
        h, s, v = self._to_hsv(r, g, b)
        hsv_classifier = h > 0 and \
                h < 35 and \
                s > 0.23 and \
                s < 0.68

# YCbCr 颜色模式下的判定
        y, cb, cr = self._to_ycbcr(r, g, b)
        ycbcr_classifier = 97.5 <= cb <= 142.5 and 134 <= cr <=176
# 这个公式的效果不是很好

        return ycbcr_classifier
    def _to_normalized(self, r, g, b):
        if r == 0:
            r = 0.0001
        if g == 0:
            g = 0.0001
        if b == 0:
            b = 0.0001
        _sum = float(r + g + b)
        return [r / _sum, g / _sum, b /_sum]

    def _to_ycbcr(self, r, g, b):
# 公式来源：
    http://stackoverflow.com/questions/19459831/rgb-to-ycbcr--conversion-problems
    y = .299*r + .587*g + .114*b
    cb = 128 - 0.168736*r - 0.331364*g + 0.5*b
    cr = 128 + 0.5*r - 0.418688*g - 0.081312*b
    return y, cb, cr

def _to_hsv(self, r, g, b):
    h = 0
    _sum = float(r + g +b)
    _max = float(max([r, g, b]))
    _min = float(min[r, g, b]))
    diff = float(_max - _min)
    if _sum == 0:
        _sum = 0.0001

    if _max == r:
        if diff == 0:
            h = sys.maxsize
        else:
            h = (g -b) / diff
    elif _max == g:
        h = 2 + ((g -r) /diff)
    else:
        h = 4 + ((r-g) / diff)

    h *=60
    if h < 0:
        h += 360

    return [h, 1.0 - (3.0 * (_min / _sum)), (1.0 / 3.0) * _max]

"""
self._add_merge() 方法主要是对 self.merge_regions 操作，而self.merge_regions 的元素都是包含一些 int 对象（区域号）的列表，列表中的区域号代表的区域都是待合并的区。self._add_merge() 方法接收两个区域号，将之添加到 self.merge_regions 中。

这两个区域号以怎样的形式添加，要分 3 种情况处理：

传入的两个区域号都存在于 self.merge_regions 中
传入的两个区域号有一个区域号存在于 self.merge_regions 中
传入的两个区域号都不存在于 self.merge_regions 中
具体的处理方法，见代码：

"""

    def _add_merge(self, _from, _to):
# 两个区域号赋值给类属性
        self.last_from = _from
        self.last_to = _to

# 记录 self.merge_regions 的某个索引值，初始化为-1
        from_index = -1
# 记录 self.merge_regions的某个索引值，初始化为-1
        to_index = -1

# 遍历每个self.merge_regions的元素
        for index, region in enumerate(self.merge_regions):
# 遍历元素中的每个区域号
            for r_index in region:
                if r_index == from:
                    from_index = index
                if r_index == _to:
                    to_index = index

        # 若两个区域号都存在于self.merge_regions中
        if from_index != -1 and to_index != -1:
# 如果两个区域号分存在于两个列表中，那么就合并这两个列表
            if from_index != to_index:
                self.merge_regions[from_index].extend(self.merge_regions[to_index])
                del(self.merge_regions[to_index])
            return

# 若两个区域号都不存在与self.merge_regions中
        if from_index == -1 and to_index == -1:
# 创建新的区域号列表
            self.merge_regions.append([from, _to])
            return
# 若两个区域有一个存在于self.merge_regions中
        if from_index != -1 and to_index == -1:
# 将不存在与self.merge_region中的那个区域号添加到另一个区域号所在的列表
            self.merge_regions[from_index].append(_to)
            return

# 若两个待合并的区域号中有一个存在于 self.merge_regions中
        if from_index == -1 and to_index != -1:
# 将不存在与self.merge_regions中的那个区域号添加到另一个区域号所在的列表
            self.merge_regions[to_index].append(_from)
            return


