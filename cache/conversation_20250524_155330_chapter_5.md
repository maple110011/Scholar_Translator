# 3. DUAL STABILITY THEOREM

收到。

在明确全局与局部相对稳定性的概念后，我们便可探讨双重稳定性定理：若产出系统具有相对稳定性，则价格系统必然无法保持相对稳定，反之亦然。动态投入产出系统的对偶性解释可表述为如下对偶系统的"长期均衡"：

$$  
\begin{cases}  
\dot{\mathbf{p}}(t) = -\mathbf{p}(t)\mathbf{A} + \mathbf{v}(t) & \text{(price adjustment equations)} \\  
\dot{\mathbf{x}}(t) = \mathbf{B}\mathbf{x}(t) - \mathbf{y}(t) & \text{(quantity adjustment equations)}  
\end{cases}  
$$

\begin{array}{r}{\phi=(1+\pi)\left(\phi A + r\phi B - \dot{\phi}B + w a_{o}\right)}\end{array}

$$
\begin{array}{r}
{\phi=(1+\pi)\left(\phi A + r\phi B - \dot{\phi}B + w a_{o}\right)}
\end{array}
$$

其中，$\boldsymbol{\phi}$ 为价格向量，$\pi$ 为利润率，$A$ 为原系统的投入产出矩阵，$B$ 为存量-流量矩阵，$\gamma$ 为利率，$\dot{\boldsymbol{\phi}}$ 为价格水平$\phi$的一阶时间导数向量，$w$ 为工资率，$a_{o}$ 为劳动需求向量：简言之，各部门的价格水平等于该部门单位产出的成本——即期成本$\phi A$、利息支出$\boldsymbol{\gamma}_{\phi B}$、资本损失$\dot{\phi}B$、工资成本${w a}_{o}$——乘以（1+利润率）。此对偶系统融合了Morishima [9] 和 Solow [12] 提出的对偶解释特征。根据定义，在长期均衡中$\scriptstyle{\pi=0}$，即所有部门的利润消失。为表述方便，我们设利率$\scriptstyle\pmb{\gamma}=0$。在封闭模型中，利率对价格的相对稳定性没有影响。

我们首先讨论封闭系统，即一种将家庭部门视为与其他"部门"处理方式相同的模型。其产出为劳动服务，其投入为消费商品。我们所考虑的模型可表述为：

$$  
\begin{cases}  
\dot{\mathbf{p}}(t) = -\mathbf{p}(t)\mathbf{A} + \mathbf{v}(t) & \text{（价格调整方程）} \\  
\dot{\mathbf{x}}(t) = \mathbf{B}\mathbf{x}(t) - \mathbf{y}(t) & \text{（数量调整方程）}  
\end{cases}  
$$

\hbar=\hbar{\cal A}-\dot{\phi}{\cal B}。

$$  
\hbar=\hbar{\cal A}-\dot{\phi}{\cal B}  
$$

解出$\dot{\boldsymbol{\phi}}$，可得：

解出$\dot{\boldsymbol{\phi}}$，可得：  
$$  
\hbar=\hbar{\cal A}-\dot{\phi}{\cal B}  
$$

$$
\dot{\phi} = -\rlap{/}P(I - A)B^{-1} = \phi D~
$$

$$  
\dot{\phi} = -\rlap{/}P(I - A)B^{-1} = \phi D~  
$$

但$-D^{-1}$为弗罗贝尼乌斯矩阵，因此存在一组均衡相对价格及与之关联的矩阵$D$的负特征值$-\varrho$，使得所有价格均为正值。由此可得以下定理：

**双重稳定性定理**：对于一阶以上系统，若产出系统具有全局相对稳定性，则价格系统必然呈现全局相对不稳定性，反之亦然。

**局部相对稳定性定理**：若系统阶数大于$C$中实部等于$\gamma$的一阶特征根数量，则当产出系统具有局部相对稳定性时，价格系统必然呈现局部相对不稳定性，反之亦然。

**证明**：令$s$为$C$实部小于$\gamma$的特征根数量，$u_{1}$为其实部大于$\gamma$的特征根数量，$u_{2}$为实部等于$\gamma$但指数大于一的特征根数量，$n$为实部等于$\gamma$且指数为一的$C$特征根数量。令$D$及$-\varrho$对应的特征根数量分别为$s^{\prime}$、$u_{1}^{\prime}$、$u_{2}^{\prime}$和$n^{\prime}$。

**证明**：产出系统具有全局相对稳定性的充要条件为$u_{1}+u_{2}+n-1=0$，价格系统对应的类似条件为$u_{1}^{\prime}+u_{2}^{\prime}+n^{\prime}-1=0$。这些结论可直接由等价性定理及第895页定理推导得出。注意到$C$与$-D$的特征根具有同源性[8]，且$\gamma=\varrho$。因此显然可得$s=u_{1}^{\prime}$，$u_{1}=s^{\prime}$，$u_{2}=u_{2}^{\prime}$，$n=n^{\prime}$。多部门增长理论的全局相对稳定性意味着$s^{\prime}+u_{2}^{\prime}+n^{\prime}-1=0$。当系统阶数大于一时，$u^{\prime}\neq0$，此时价格系统呈现不稳定性。

**证明**：动态投入产出系统具有局部相对稳定性的充要条件是$u_{1}+u_{2}=0$，而动态价格理论中局部相对稳定性的充要条件为$u_{1}^{\prime}+u_{2}^{\prime}=0$。若$u_{1}+u_{2}=0$，则$s^{\prime}=0$。当系统阶数大于$n^{\prime}$时，$u_{1}^{\prime}+u_{2}^{\prime}\neq0$，此时价格系统不稳定；若系统阶数为$n^{\prime}$，则价格系统具有局部相对稳定性<sup>8</sup>。

我们已证明全局相对稳定性与局部相对稳定性

<sup>8</sup> 令$s$（即$u_{1}^{\prime}$）与$u_{1}$（即$s^{\prime}$）取正值。由于假设${\boldsymbol{x}}(0)$与$\boldsymbol{p}(0)$相互独立，此时实际路径${\boldsymbol{x}}(t)$与${\boldsymbol{\phi}}(t)$可能对于某些初始条件是稳定的。

产出系统的（全局/局部）相对稳定性在相同意义上暗示价格系统的不稳定性；反之亦然的结论同理可得<sup>9</sup>。

