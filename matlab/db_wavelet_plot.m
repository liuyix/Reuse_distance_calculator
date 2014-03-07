function  D = db_wavelet_plot(X)

% Input: reuse_distance向量
% Output: 无
%% code... 
level = 6;
wname = 'db6';
[C, L] = wavedec(X, level, wname);
D = detcoef(C, L, 6);
plot(D);

end