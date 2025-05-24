# 2.RELATIVE STABILITY

收到。

双重稳定性定理的验证需要一套明确的相对稳定性理论。众所周知，线性微分方程系统的主导根最终决定了系统的演变轨迹[7]。这一事实被应用于提取矩阵特征根的常用幂方法中[6]。动态投入产出系统相对稳定性问题的核心在于：存在一个具有特殊意义的给定解，即所有元素均为正的平衡增长（或恒定相对价格）解；此外，在投入产出矩阵或存量-流量矩阵的温和约束条件下，该解具有唯一性。在何种条件下，该解将主导系统的行为？问题的关键不在于其他根与零的关系（或在差分方程情形下与模为一的关系），而在于这些根与经济均衡增长率或利率的关系。例如，假设经济均衡增长率为10%，同时存在增长率为5%的瞬态过程。最终，解中瞬态分量的比例将变得可忽略不计；在增长过程中，唯有相对比例具有实质意义。尽管瞬态分量本身在增长，但相对于与均衡增长率相关联的解分量而言，其占比将逐渐衰减。这些观点可作如下形式化表述。

设$\scriptstyle x=A x+B{\dot{x}}$表示一个封闭、动态的投入产出系统，其中$x$为产出水平向量，$A$为投入产出矩阵，$B$为存量-流量矩阵，$\dot{x}$为$x$对时间的一阶导数。令$C=B^{-1}(I-A)$，该系统的解可表示为：

$$

$$x(t)=e^{C t}x(0)$$

$$

其中假定$B$为非奇异矩阵。若$B$为奇异矩阵，则可应用标准方法将系统阶数降至$C$的秩[6]。我们假定已完成该降阶过程。假设$A$为不可分解矩阵，则$C^{-1}$为不可分解的弗罗贝尼乌斯矩阵。因此，$C$存在一个实数、正数、单重特征根$\gamma$，且该$\gamma$对应唯一的正特征向量$\xi$[1]。特解$e^{\gamma t}\xi$被称为平衡增长解。

相对稳定性理论可概括如下：

定义：当且仅当对任意$\varepsilon>0$，存在时间$T$，使得对所有$t>T$及系统中每个初始条件$x(0)\geq0$，有  
$$  
\left| \frac{x_i(t)}{e^{\gamma t}\xi_i} -1 \right| < \varepsilon \quad (i=1,2,\cdots,n)  
$$  
时，线性微分方程组$\dot{x}=C x$的唯一正解称为全局相对稳定的。

$$  
\left| \frac{x_i(t)}{e^{\gamma t}\xi_i} -1 \right| < \varepsilon \quad (i=1,2,\cdots,n)  
$$

\left|\frac{x_{i}(t)}{x_{1}(t)}-\frac{\xi_{i}}{\xi_{1}}\right|<\varepsilon

$$  
\left|\frac{x_{i}(t)}{x_{1}(t)}-\frac{\xi_{i}}{\xi_{1}}\right|<\varepsilon  
$$

其中$x_{i}(t)$为通解$\boldsymbol{x}(t)=e^{C t}\boldsymbol{x}(0)$的第$i$个分量（$x(0)\geqslant0$），而$e^{\gamma t}\xi_{i}$为特征解$e^{\gamma t}\xi$的第$i$个分量。可选取$x(t)$的第一个分量为该解的任意非零分量。在任意时刻$t$，该解中至少存在一个这样的非零分量。

我们亦可定义局部相对稳定性：

定义：当且仅当对任意$\varepsilon>0$，存在向量$\delta>0$，使得对于满足$|\varphi|<\delta$的任意扰动，存在时间$T$，使得对所有$t>T$有  
$$  
\left| \frac{x_i(t)}{e^{\gamma t}\xi_i} -1 \right| < \varepsilon \quad (i=1,2,\cdots,n)  
$$  
时，线性微分方程组$\dot{x}=C x$的唯一正解$e^{\gamma t}\xi$称为局部相对稳定的。

定义：当且仅当对任意$\varepsilon>0$，存在向量$\delta>0$，使得对于满足$|\varphi|<\delta$的任意扰动，存在时间$T$，使得对所有$t>T$有  
$$  
\left| \frac{x_i(t)}{e^{\gamma t}\xi_i} -1 \right| < \varepsilon \quad (i=1,2,\cdots,n)  
$$  
时，线性微分方程组$\dot{x}=C x$的唯一正解$e^{\gamma t}\xi$称为局部相对稳定的。

\left|\frac{x_{i}(t)}{x_{1}(t)}-\frac{\xi_{i}}{\xi_{1}}\right|<\varepsilon

$$  
\left|\frac{x_{i}(t)}{x_{1}(t)}-\frac{\xi_{i}}{\xi_{1}}\right|<\varepsilon  
$$

其中$x_{i}(t)$为通解$x(t)$的第$i$个分量▪▪

且

其中$x_{i}(t)$为通解$x(t)$的第$i$个分量，且

\begin{array}{c}  
{{x(t)=e^{C t}\left(\xi+\varphi\right)}}\\  
{{}}\\  
{{\xi+\varphi\geqslant0}}  
\end{array}

\begin{array}{c}  
x(t)=e^{C t}\left(\xi+\varphi\right)\\  
\\  
\xi+\varphi\geqslant0  
\end{array}

若矩阵$C$不存在其他实部等于$\gamma$的特征根，则相对稳定性理论可归纳为以下命题：

等价性定理：以下三个命题等价：（1）$e^{\gamma t}\xi$具有局部相对稳定性；

（2）$e^{\gamma t}\xi$具有全局相对稳定性；

（3）矩阵$C$的所有特征根的实部均小于$\gamma$。

若存在实部等于$\gamma$的特征根，则全局相对稳定性不再等价于局部相对稳定性。对于初始条件中包含与实部等于$\gamma$的特征值相关联的特征向量且该向量具有非零常数系数的情形，系统将永远无法实现全局稳定性。这些结论可归纳为以下命题：

定理：若矩阵$C$存在若干实部等于$\gamma$的特征根，且不存在实部大于$\gamma$的特征根，则当且仅当所有此类特征根具有指数一时，$e^{\gamma t}\xi$才具有局部相对稳定性<sup>6</sup>；此外，$e^{\gamma t}\xi$不具有全局相对稳定性。

