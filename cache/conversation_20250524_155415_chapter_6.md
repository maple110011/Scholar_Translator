# 4. DUAL INSTABILITY IN THE OPEN SYSTEM

收到。

开放系统允许产出与价格体系同时稳定的可能性。为实现这一现象，与均衡增长率对应的解必须主导所有其他解，且对偶方程齐次部分的所有解必须全部衰减消失，最终由非齐次项决定的正值价格体系得以留存。我们由此得到

**定理**：欲使动态投入产出系统及其对偶系统具有全局相对稳定性，当且仅当矩阵$C$中除$\gamma$外的任意根$\alpha+\beta i$满足以下条件：

$$  
\alpha < \gamma; \quad \text{若} \ \alpha = \gamma, \ \text{则虚部} \ \beta = 0.  
$$

$$0 \leqslant r < \alpha < \gamma\ 。$$

$$0 \leqslant r < \alpha < \gamma\ 。$$

该条件表明：对于单位劳动成本的非负向量，必然存在与之对应的正价格体系。

**证明**：为验证上述结论，需考察开放系统及其对偶系统：

$$

$$x = A x + B\dot{x} + y，$$

$$  
x = A x + B\dot{x} + y，  
$$

$$x = A x + B\dot{x} + y，$$

$$
\begin{array}{r}
\dot{p} = \phi A + r\phi B - \dot{p}B + w a_{o},
\end{array}
$$

$$
\begin{array}{r}
\dot{p} = \phi A + r\phi B - \dot{p}B + w a_{o},
\end{array}
$$

其中$y$为最终需求向量，其余变量定义与第3节相同。假设$y$、$w a_{o}$均为非负向量，且各自至少包含一个正元素。若对于矩阵$C$中除$\gamma$外的所有特征根$\alpha+\beta i$，均有$0 \leqslant r < \alpha < \gamma$，则该系统及其对偶系统显然分别具有相对稳定性和稳定性——由于$\gamma$是产出系统的主导特征根，且在对偶系统的解中矩阵$-(I - A - r B)B^{-1}$的所有根

$$

$$\dot{p} = -\rlap{/}p(I - A - r B)B^{-1} + w a_{0}B^{-1},$$

$$\dot{p} = -\rlap{/}p(I - A - r B)B^{-1} + w a_{0}B^{-1},$$

**9** 研究结论可推广至差分方程系统。例如，考察$\boldsymbol{r}=0$时的封闭型索洛模型[12]：

$$\dot{p} = -\rlap{/}p(I - A - r B)B^{-1} + w a_{0}B^{-1},$$

$$x_{t} = A x_{t} + B(x_{t+1} - x_{t}) = B^{-1}(I - A + B)x_{t-1} = (C + I)x_{t-1},$$

$$x_{t} = A x_{t} + B(x_{t+1} - x_{t}) = B^{-1}(I - A + B)x_{t-1} = (C + I)x_{t-1},$$

$$x_{t} = A x_{t} + B(x_{t+1} - x_{t}) = B^{-1}(I - A + B)x_{t-1} = (C + I)x_{t-1},$$  
及其对偶系统：

$$x_{t} = A x_{t} + B(x_{t+1} - x_{t}) = B^{-1}(I - A + B)x_{t-1} = (C + I)x_{t-1},$$  
及其对偶系统：

$$
\begin{array}{r}
\gamma_{t} = \phi_{t}{}^{A} - (\phi_{t} - \phi_{t-1})B = \phi_{t-1}B(I - A + B)^{-1} = \phi_{t-1}(I - D)^{-1}.
\end{array}
$$

$$
\begin{array}{r}
\gamma_{t} = \phi_{t}{}^{A} - (\phi_{t} - \phi_{t-1})B = \phi_{t-1}B(I - A + B)^{-1} = \phi_{t-1}(I - D)^{-1}.
\end{array}
$$

核心结论在于：$1+\gamma$是产出系统的均衡增长率，而$1/(1+\varrho)$为价格系统中对应唯一正相对价格的特征根。若存在模大于$1+\gamma$的根，则对偶系统中必然存在模小于$1/(1+\varrho)$的根。反之，若存在模小于$1/(1+\varrho)$的根，则对偶系统中必然存在模大于$1+\gamma$的根——这一逆向关系亦易于验证。此即**对偶稳定性定理**。

均为负值，故解趋近于

均为负值，故解趋近于

$$
\begin{array}{r}
\phi = w a_{o}(I - A - {r}B)^{-1}.
\end{array}
$$

$$
\begin{array}{r}
\phi = w a_{o}(I - A - {r}B)^{-1}。
\end{array}
$$

此外，当且仅当$(I - A - r B)^{-1}$由正元素构成时，对于任何非负且至少含有一个正元素的$\boldsymbol{w a_{o}}$，价格体系均为正值。该结论成立的充要条件是$\gamma < \gamma$<sup>10</sup>，而这一条件由$\boldsymbol{r} < \boldsymbol{\alpha} < \boldsymbol{\gamma}$隐含成立。至此已完成充分性证明；必要性证明可通过以下观察获得：若$\alpha \geqslant \gamma$，则产出系统具有全局相对不稳定性；若$\alpha \leqslant r$，则对偶系统的稳态解在常规意义下具有全局不稳定性。条件$\prime \geqslant 0$是结果具备经济学解释的必要前提，$\alpha < 0$则意味着价格体系在任何非负利率下均呈现全局不稳定性<sup>11</sup>。

此处需阐明一个特殊结论。由于$\gamma$是矩阵$C$中模长最小的根，则$\alpha$必为某个复根$\alpha+\beta i$的实部，且该复根的模长$\sqrt{\alpha^{2}+\beta^{2}}$大于$\gamma$。但若系统中存在除$\gamma$外的任何实根，则该系统必然具有双重不稳定性特征。由于复根总是成对出现，这意味着任何偶数阶开放系统必然不稳定——其价格体系或产出体系或两者同时失稳。在奇数部门的开放系统中，仅当所有根（除$\gamma$外）均为复根且每个复根的实部满足$\alpha<\gamma$时，价格与产出才能同时稳定。  

"商品种类数量影响实际经济系统稳定性"这一观点看似缺乏合理性。然而，要构造出满足我们所述条件（奇数阶且复根实部符合特定约束）的系统，其可能性微乎其微。除却这种极端特例，索洛猜想在普遍意义下成立。

加州大学伯克利分校

